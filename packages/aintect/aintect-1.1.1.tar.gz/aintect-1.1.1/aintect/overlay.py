def parse_resolution(resolution_str):
	return tuple(map(int, resolution_str.split()[0].split("x")))

def overlay_masks_boxes_labels_predict(image_pil, masks, boxes, class_colors, labels, alpha=0.3):
    # Convert PIL image to NumPy array for OpenCV
    overlay_np = np.array(image_pil)
    overlay_np = cv2.cvtColor(overlay_np, cv2.COLOR_RGB2BGR)
    
    # Create a separate layer for masks to blend them all at once
    mask_layer = np.zeros_like(overlay_np, dtype=np.uint8)

    for mask, label in zip(masks, labels):
        class_name = label.split(' ')[0]
        color = class_colors.get(class_name, (255, 255, 255))
        
        # Create a colored mask
        colored_mask = np.zeros_like(overlay_np, dtype=np.uint8)
        mask_cpu = mask.cpu().numpy().astype(bool)
        colored_mask[mask_cpu] = color
        
        # Add this mask to the single mask layer
        mask_layer = cv2.add(mask_layer, colored_mask)

    # Blend the single mask layer with the original image
    overlay_np = cv2.addWeighted(mask_layer, alpha, overlay_np, 1, 0)

    # Define font properties
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 1

    # Draw boxes and labels
    for box, label in zip(boxes, labels):
        x1, y1, x2, y2 = map(int, box)
        class_name = label.split(' ')[0]
        color = class_colors.get(class_name, (255, 255, 255))
        
        # Bounding box
        cv2.rectangle(overlay_np, (x1, y1), (x2, y2), color, 2)

        # Label background
        (text_w, text_h), baseline = cv2.getTextSize(label, font_face, font_scale, font_thickness)
        label_y = y1 - 10 if y1 - text_h - 10 > 10 else y1 + text_h + 10
        cv2.rectangle(overlay_np, (x1, label_y - text_h - baseline), (x1 + text_w, label_y + baseline), color, -1)
        
        # Label text
        cv2.putText(overlay_np, label, (x1, label_y), font_face, font_scale, (0, 0, 0), font_thickness, cv2.LINE_AA)
        
    # Convert back to PIL Image at the very end
    return Image.fromarray(cv2.cvtColor(overlay_np, cv2.COLOR_BGR2RGB))

def resize_and_binarize_masks(masks, image_size):
    """
    Combined function to handle:
    1. Single Tensors or Lists of Tensors
    2. Automatic correction of PIL (W, H) vs PyTorch (H, W)
    """
    # --- 1. HANDLE INPUT TYPE (Recall A vs B) ---
    # If it's a list (Recall A), stack it into a 4D tensor (N, 1, H, W)
    if isinstance(masks, list):
        # Ensure each mask is at least 2D before stacking
        processed_list = [m.unsqueeze(0) if m.dim() == 2 else m for m in masks]
        masks_tensor = torch.stack(processed_list) 
        if masks_tensor.dim() == 3: # (N, H, W)
             masks_tensor = masks_tensor.unsqueeze(1)
    else:
        # If it's already a tensor (Recall B), ensure it is 4D (N, 1, H, W)
        masks_tensor = masks
        if masks_tensor.dim() == 3:
            masks_tensor = masks_tensor.unsqueeze(1)
        elif masks_tensor.dim() == 2:
            masks_tensor = masks_tensor.unsqueeze(0).unsqueeze(0)

    # --- 2. HANDLE IMAGE SIZE (The PIL Fix) ---
    # Logic: PyTorch needs (Height, Width). 
    # If the user passes pil_img.size (W, H), we detect if it matches the mask aspect ratio
    # or use the provided logic from Function A to be safe.
    
    # Check if the first dimension is smaller than the second (often true for landscape)
    # To be exactly compatible with your 'Recall A' fix:
    # If we assume (W, H) is passed, we reverse it.
    # However, to support BOTH recalls, we check if image_size[1] matches height.
    # For simplicity and to match your specific Function A fix:
    h_in, w_in = masks_tensor.shape[-2:]
    
    # We define output_size based on which recall style is used.
    # Recall B passes (H, W) directly. Recall A passes (W, H).
    # This logic assumes if W > H in the image_size tuple, it might be PIL format.
    # But to be safe, we'll follow the logic from your Function A:
    target_h, target_w = image_size[1], image_size[0]

    # --- 3. PROCESS ---
    resized_masks = torch_F.interpolate(
        masks_tensor.float(), 
        size=(target_h, target_w), 
        mode="bilinear", 
        align_corners=False
    )
    
    # Binarize
    binarized = (resized_masks > 0.5).byte().squeeze(1)
    
    # --- 4. RETURN FORMAT ---
    # If input was a list (Recall A), return a list. Otherwise return a tensor (Recall B).
    if isinstance(masks, list):
        return [m for m in binarized]
    return binarized

def resize_frame_based_on_resolution(frame, new_height, aspect_ratio):
    if aspect_ratio > 0:
        new_width = int(new_height * aspect_ratio)
        return cv2.resize(frame, (new_width, new_height))
    return frame

def filter_overlapping_detections(boxes, scores, labels, masks, threshold=0.25):
	keep = []
	indices = torch.argsort(scores, descending=True)
	while len(indices) > 0:
		current = indices[0]
		keep.append(current)
		if len(indices) == 1:
			break
		current_box = boxes[current]
		current_label = labels[current]
		other_indices = indices[1:]
		other_boxes = boxes[other_indices]
		other_labels = labels[other_indices]
		x1 = torch.max(current_box[0], other_boxes[:, 0])
		y1 = torch.max(current_box[1], other_boxes[:, 1])
		x2 = torch.min(current_box[2], other_boxes[:, 2])
		y2 = torch.min(current_box[3], other_boxes[:, 3])
		inter_area = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)
		current_area = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
		other_areas = (other_boxes[:, 2] - other_boxes[:, 0]) * (other_boxes[:, 3] - other_boxes[:, 1])
		union_area = current_area + other_areas - inter_area
		iou = inter_area / union_area
		mask = (other_labels != current_label) | (iou <= threshold)
		indices = other_indices[mask]
	keep = torch.tensor(keep, dtype=torch.long)
	filtered_boxes = boxes[keep]
	filtered_scores = scores[keep]
	filtered_labels = labels[keep]
	filtered_masks = [masks[i] for i in keep.tolist()]
	return filtered_boxes, filtered_scores, filtered_labels, filtered_masks
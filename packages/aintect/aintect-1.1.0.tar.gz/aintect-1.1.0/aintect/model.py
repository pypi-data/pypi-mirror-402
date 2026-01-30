import torch
import os
import numpy as np
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models.detection import maskrcnn_resnet50_fpn, MaskRCNN
from torchvision.models.detection.anchor_utils import AnchorGenerator
from torchvision.transforms import functional as F
from torchvision.ops import FeaturePyramidNetwork
from torchvision.models.detection import MaskRCNN_ResNet50_FPN_Weights
from torch.optim.lr_scheduler import  LambdaLR
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights, ResNet18_Weights

class CustomFastRCNNPredictor(FastRCNNPredictor):
    def forward(self, x):
        logits = super().forward(x)
        return logits  # Only return logits

class LogitsExtractor(torch.nn.Module):
    def __init__(self, predictor):
        super().__init__()
        self.predictor = predictor
        self.saved_logits = None

    def forward(self, x):
        logits = self.predictor(x)
        if isinstance(logits, tuple):  # Handle case where predictor returns a tuple
            self.saved_logits = logits[0]  # Save only classification scores
        else:
            self.saved_logits = logits
        return logits

################################################################################################################################

class ModelFactory:
    def __init__(self, num_classes, device=None):
        self.num_classes = num_classes
        self.device = device if device else torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    def create_model(self, modelType, train_dataset, previous_model_path=None, lr=1e-4, weight_decay=1e-4, num_epochs=10, train_loader=None):
        if modelType == 0:
            print("RestNet-50 as backbone")  

            anchor_sizes = ((16,), (32,), (64,), (128,), (256,))  # Smaller base sizes
            aspect_ratios = ((0.5, 1.0, 2.0),) * len(anchor_sizes)
            anchor_generator = AnchorGenerator(sizes=anchor_sizes, aspect_ratios=aspect_ratios)

            model = maskrcnn_resnet50_fpn(weights=MaskRCNN_ResNet50_FPN_Weights.DEFAULT, rpn_anchor_generator=anchor_generator)
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            base_predictor = FastRCNNPredictor(in_features, train_dataset.num_classes)  # +1 for background
            model.roi_heads.box_predictor = LogitsExtractor(base_predictor)

        elif modelType == 1:  # MobileNetV3 Backbone
            print("MobileNetV3 as backbone")

            # Extract features from MobileNetV3
            mobilenet = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.DEFAULT)
            mobilenet_backbone = mobilenet.features

            # Define the feature layers to use for FPN
            layers_to_extract = [3, 6, 12]  # Example layers, adjust based on your requirements
            feature_channels = [mobilenet_backbone[i].out_channels for i in layers_to_extract]

            # Create a dictionary of extracted feature layers
            return_layers = {str(i): str(idx) for idx, i in enumerate(layers_to_extract)}
            backbone = torch.nn.Sequential(*mobilenet_backbone)
            backbone_out = {return_layers[str(i)]: backbone[i] for i in layers_to_extract}

            # Define anchor sizes and aspect ratios for each feature map
            num_feature_maps = len(layers_to_extract)  # Ensure this matches the number of feature maps from the FPN
            anchor_sizes = tuple([(32 * (2 ** i),) for i in range(num_feature_maps)])  # Scaled sizes
            aspect_ratios = ((0.5, 1.0, 2.0),) * num_feature_maps  # Same ratios for all feature maps
            # print(f"[DEBUG] Number of feature maps: {len(feature_channels)}")
            # print(f"[DEBUG] Anchor sizes: {anchor_sizes}")
            # print(f"[DEBUG] Aspect ratios: {aspect_ratios}")

            # Create the AnchorGenerator
            anchor_generator = AnchorGenerator(sizes=anchor_sizes, aspect_ratios=aspect_ratios)

            # Wrap the backbone and FPN
            fpn_out_channels = 256
            fpn = FeaturePyramidNetwork(feature_channels, out_channels=fpn_out_channels)
            backbone_with_fpn = BackboneWithFPNWrapper(mobilenet_backbone, fpn, fpn_out_channels)

            # Create the MaskRCNN model with the custom anchor generator
            model = MaskRCNN(
                backbone_with_fpn,
                num_classes=train_dataset.num_classes,
                rpn_anchor_generator=anchor_generator,
            )

            # Adjust the predictor for your number of classes
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            base_predictor = FastRCNNPredictor(in_features, train_dataset.num_classes)
            model.roi_heads.box_predictor = LogitsExtractor(base_predictor)

        elif modelType == 2:  # ResNet18 Backbone
            print("ResNet-18 as backbone")

            # Load pre-trained resnet18 and extract layers
            resnet18 = resnet18(weights=ResNet18_Weights.DEFAULT)

            # Remove fully connected layers and use up to layer4
            backbone = torch.nn.Sequential(*list(resnet18.children())[:-2])  # Exclude avgpool and fc

            # Get the number of output channels from the last layer
            backbone.out_channels = 512

            # Define the anchor generator
            anchor_generator = AnchorGenerator(
                sizes=((32, 64, 128, 256, 512),),
                aspect_ratios=((0.5, 1.0, 2.0),) * 5
            )

            # Define the ROI pooler
            roi_pooler = torchvision.ops.MultiScaleRoIAlign(
                featmap_names=['0'], output_size=7, sampling_ratio=2
            )

            # Define the mask pooler (optional for mask prediction)
            mask_roi_pooler = torchvision.ops.MultiScaleRoIAlign(
                featmap_names=['0'], output_size=14, sampling_ratio=2
            )

            # Create the MaskRCNN model
            model = MaskRCNN(
                backbone=backbone,
                num_classes=train_dataset.num_classes,
                rpn_anchor_generator=anchor_generator,
                box_roi_pool=roi_pooler,
                mask_roi_pool=mask_roi_pooler
            )

            # Adjust the predictor for your number of classes
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            base_predictor = FastRCNNPredictor(in_features, train_dataset.num_classes)
            model.roi_heads.box_predictor = LogitsExtractor(base_predictor)

        device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        # Load the weights and automatically handle the classification head
        if previous_model_path and os.path.exists(previous_model_path):
            print(f"Loading weights from: {previous_model_path}")
            # Load the weights onto the CPU first to avoid GPU memory issues
            state_dict = torch.load(previous_model_path, map_location='cpu')

            # Check if the number of classes in the pre-trained model's head matches the new dataset
            old_num_classes = state_dict['roi_heads.box_predictor.predictor.saved_logits.weight'].shape[0]

            if old_num_classes != train_dataset.num_classes:
                print(f"🧠 Head Mismatch: Old model has {old_num_classes} classes, new dataset has {train_dataset.num_classes}.")
                print("Removing old classification head...")
                # Remove the weights of the old head from the state dictionary
                for key in ['roi_heads.box_predictor.predictor.saved_logits.weight', 'roi_heads.box_predictor.predictor.saved_logits.bias']:

                    if key in state_dict:

                        del state_dict[key]

                # Load the rest of the weights (the backbone)
                model.load_state_dict(state_dict, strict=False)

                # Now, create and attach a new, randomly initialized head
                print("Attaching new head...")
                in_features = model.roi_heads.box_predictor.cls_score.in_features
                new_predictor = FastRCNNPredictor(in_features, train_dataset.num_classes)
                model.roi_heads.box_predictor = LogitsExtractor(new_predictor)

            else:
                print("✅ Head Match: Class numbers are the same. Loading all weights.")
                model.load_state_dict(state_dict)
        else:
            print("🔥 No previous model found, starting from scratch.")

        model.to(device)

        # Load the weights
        if os.path.exists(previous_model_path):
            print(f"Loading weights from: {previous_model_path}")
            model.load_state_dict(torch.load(previous_model_path))
        else:
            print("No previous model found, starting from scratch.")

        params = [p for p in model.parameters() if p.requires_grad]

        # Define optimizer
        optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)

        # Total number of steps in the training
        total_steps = num_epochs * len(train_loader)

        # Warmup steps (e.g., 10% of total steps)
        warmup_steps = int(0.1 * total_steps)

        # Define the warmup function
        def warmup_cosine_decay(step):
            if step < warmup_steps:
                # Linear warmup
                return step / warmup_steps
            else:
                # Cosine annealing decay
                return 0.5 * (1 + np.cos(np.pi * (step - warmup_steps) / (total_steps - warmup_steps)))

        # Combine warmup with cosine annealing
        scheduler = LambdaLR(optimizer, lr_lambda=warmup_cosine_decay)


class BackboneWithFPNWrapper(torch.nn.Module):
    def __init__(self, backbone, fpn, out_channels, return_layers):
        super().__init__()
        self.body = backbone
        self.fpn = fpn
        self.out_channels = out_channels
        self.return_layers = return_layers  # Store the layer mapping here

    def forward(self, x):
        features = {}
        # Iterate through the backbone modules
        for name, module in self.body.named_children():
            x = module(x)
            if name in self.return_layers:
                # Map the original layer name to the FPN key (e.g., "3" -> "0")
                features[self.return_layers[name]] = x
        
        return self.fpn(features)
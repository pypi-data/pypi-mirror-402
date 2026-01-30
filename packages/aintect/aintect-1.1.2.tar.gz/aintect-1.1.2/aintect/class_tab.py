class ImagePreprocessingTab(QWidget):
    params_changed = Signal(float, int, float, float, float)  # exp, hue, sat, bri, con
    contrast_mode_changed = Signal(bool)
    wb_mode_changed = Signal(str)  # <--- NEW SIGNAL
    load_defaults_requested = Signal()
    
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        params_form = QFormLayout()
        title_lbl = QLabel("<b>Image Preprocessing Parameters</b>")
        main_layout.addWidget(title_lbl)
        main_layout.addLayout(params_form)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 20pt; font-weight: bold;")
        
        # Exposure
        self.exp_slider = QSlider(Qt.Orientation.Horizontal)
        self.exp_slider.setRange(2, 50_000)
        self.exp_slider.setValue(1000)
        self.exp_edit = QLineEdit("1000")
        params_form.addRow("Exposure (µs)", self._create_hbox(self.exp_slider, self.exp_edit))
        
        # Hue
        self.hue_slider = QSlider(Qt.Orientation.Horizontal)
        self.hue_slider.setRange(-180, 180)
        self.hue_slider.setValue(0)
        self.hue_edit = QLineEdit("0")
        params_form.addRow("Hue", self._create_hbox(self.hue_slider, self.hue_edit))
        
        # Saturation
        self.sat_slider = QSlider(Qt.Orientation.Horizontal)
        self.sat_slider.setRange(0, 20)
        self.sat_slider.setValue(10)
        self.sat_edit = QLineEdit("1.000")
        params_form.addRow("Saturation", self._create_hbox(self.sat_slider, self.sat_edit))
        
        # Brightness
        self.bri_slider = QSlider(Qt.Orientation.Horizontal)
        self.bri_slider.setRange(-1000, 1000)
        self.bri_slider.setValue(0)
        self.bri_edit = QLineEdit("0.000")
        params_form.addRow("Brightness", self._create_hbox(self.bri_slider, self.bri_edit))

        # Contrast
        self.con_slider = QSlider(Qt.Orientation.Horizontal)
        self.con_slider.setRange(-1000, 1000)
        self.con_slider.setValue(0)
        self.con_edit = QLineEdit("0.000")
        params_form.addRow("Contrast", self._create_hbox(self.con_slider, self.con_edit))
        
        # --- NEW WHITE BALANCE COMBO ---
        self.wb_combo = QComboBox()
        self.wb_combo.addItems(["Once", "Continuous", "Off"])
        params_form.addRow("Balance White Auto", self.wb_combo)
        # -------------------------------

        self.use_scurve_checkbox = QCheckBox("Use S-Curve Contrast")
        params_form.addRow("", self.use_scurve_checkbox)

        self.defaults_btn = QPushButton("Load Defaults")
        main_layout.addWidget(self.defaults_btn)
        main_layout.addStretch()

        self._connect_signals()

    def _connect_signals(self):
        self.exp_slider.valueChanged.connect(self._emit_param_change)
        self.hue_slider.valueChanged.connect(self._emit_param_change)
        self.sat_slider.valueChanged.connect(self._emit_param_change)
        self.bri_slider.valueChanged.connect(self._emit_param_change)
        self.con_slider.valueChanged.connect(self._emit_param_change)
        self.use_scurve_checkbox.stateChanged.connect(lambda: self.contrast_mode_changed.emit(self.use_scurve_checkbox.isChecked()))
        
        # Connect White Balance Signal
        self.wb_combo.currentTextChanged.connect(self.wb_mode_changed.emit)

        self.defaults_btn.clicked.connect(self.load_defaults_requested.emit)
        
        self._connect_slider_edit(self.exp_slider, self.exp_edit, is_float=False)
        self._connect_slider_edit(self.hue_slider, self.hue_edit, factor=1, is_float=False)
        self._connect_slider_edit(self.sat_slider, self.sat_edit, factor=10.0)
        self._connect_slider_edit(self.bri_slider, self.bri_edit, factor=1000.0)
        self._connect_slider_edit(self.con_slider, self.con_edit, factor=1000.0) 

    def _emit_param_change(self):
        self.params_changed.emit(self.exp_slider.value(), self.hue_slider.value(), self.sat_slider.value() / 10.0, self.bri_slider.value() / 1000.0, self.con_slider.value() / 1000.0)

    def set_to_defaults(self):
        # Block signals
        widgets = [self.exp_slider, self.bri_slider, self.con_slider, self.sat_slider, self.hue_slider, self.use_scurve_checkbox, self.wb_combo]
        for w in widgets: w.blockSignals(True)
            
        self.exp_slider.setValue(1000)
        self.bri_slider.setValue(0)
        self.con_slider.setValue(0)
        self.sat_slider.setValue(10)
        self.hue_slider.setValue(0)
        self.use_scurve_checkbox.setChecked(False)
        self.wb_combo.setCurrentText("Once") # Default WB
        
        self.exp_edit.setText("1000")
        self.bri_edit.setText("0.000")
        self.con_edit.setText("0.000")
        self.sat_edit.setText("1.000")
        self.hue_edit.setText("0")
        
        # Unblock
        for w in widgets: w.blockSignals(False)
            
        self._emit_param_change()
        self.contrast_mode_changed.emit(False)
        self.wb_mode_changed.emit("Once") # Emit default WB

    def _create_hbox(self, w1, w2): 
        layout = QHBoxLayout()
        layout.addWidget(w1)
        w2.setFixedWidth(70)
        layout.addWidget(w2)
        return layout
    
    def _connect_slider_edit(self, slider, edit, is_float=True, factor=1.0):
        slider.valueChanged.connect(lambda val: edit.setText(f"{val / factor:.3f}" if is_float else str(val)))
        edit.editingFinished.connect(lambda: slider.setValue(int(float(edit.text()) * factor) if is_float else int(edit.text())))
        edit.editingFinished.connect(self._emit_param_change)
        
    def get_settings(self):
        return {
            "exposure": self.exp_slider.value(),
            "hue": self.hue_slider.value(),
            "saturation": self.sat_slider.value(),
            "brightness": self.bri_slider.value(),
            "contrast": self.con_slider.value(),
            "wb_mode": self.wb_combo.currentText(),
            "use_scurve": self.use_scurve_checkbox.isChecked()
        }

    def set_settings(self, settings):
        # Block signals to prevent "dirty" updates while loading
        self.blockSignals(True) 
        try:
            self.exp_slider.setValue(settings.get("exposure", 1000))
            self.hue_slider.setValue(settings.get("hue", 0))
            self.sat_slider.setValue(settings.get("saturation", 10))
            self.bri_slider.setValue(settings.get("brightness", 0))
            self.con_slider.setValue(settings.get("contrast", 0))
            self.wb_combo.setCurrentText(settings.get("wb_mode", "Once"))
            self.use_scurve_checkbox.setChecked(settings.get("use_scurve", False))
            
            # Manually update text edits since signals were blocked
            self.exp_edit.setText(str(self.exp_slider.value()))
            self.hue_edit.setText(str(self.hue_slider.value()))
            self.sat_edit.setText(f"{self.sat_slider.value()/10.0:.3f}")
            self.bri_edit.setText(f"{self.bri_slider.value()/1000.0:.3f}")
            self.con_edit.setText(f"{self.con_slider.value()/1000.0:.3f}")
        finally:
            self.blockSignals(False)
        
        # Emit changes once to update the camera
        self._emit_param_change()
        self.contrast_mode_changed.emit(self.use_scurve_checkbox.isChecked())
        self.wb_mode_changed.emit(self.wb_combo.currentText())

class ModelPanel(QWidget):
    model_load_requested = Signal()
    model_stop_requested = Signal()
    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self.class_names = []
        self.class_checkboxes = {}
        self.good_checkboxes = {}
        self.ng_checkboxes = {}

        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.current_model_path = None
        self.current_meta_path = None

        # Confidence
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(0, 100)
        self.conf_edit = QLineEdit("0.50")
        form_layout.addRow("Confidence:", self._create_hbox(self.conf_slider, self.conf_edit))
        
        # # Alignment
        # self.align_slider = QSlider(Qt.Orientation.Horizontal)
        # self.align_slider.setRange(1, 100)
        # self.align_edit = QLineEdit("0.02")
        # form_layout.addRow("Alignment:", self._create_hbox(self.align_slider, self.align_edit))

        # # Major/Target Classes
        # self.bottle_combo = QComboBox()
        # self.logo_combo = QComboBox()
        # form_layout.addRow("Major Class (bottle):", self.bottle_combo)
        # form_layout.addRow("Target Class (logo):", self.logo_combo)
        
        main_layout.addLayout(form_layout)

        # Class Toggles
        self.detect_group = QGroupBox("Classes to Detect")
        detect_layout = QVBoxLayout()
        self.detect_group.setLayout(detect_layout)
        self.good_group = QGroupBox("Good Classes")
        good_layout = QVBoxLayout()
        self.good_group.setLayout(good_layout)
        self.ng_group = QGroupBox("Not Good Classes")
        ng_layout = QVBoxLayout()
        self.ng_group.setLayout(ng_layout)

        classes_layout = QHBoxLayout()
        classes_layout.addWidget(self.good_group)
        classes_layout.addWidget(self.ng_group)

        main_layout.addWidget(self.detect_group)
        main_layout.addLayout(classes_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Model")
        self.stop_btn = QPushButton("Stop/Unload Model")
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()

        self._connect_signals()

    def _connect_signals(self):
        self.load_btn.clicked.connect(self._handle_load_button_clicked) # Connect to a new handler
        self.stop_btn.clicked.connect(self._handle_stop_button_clicked) # Connect to a new handler
        # Connect all controls to emit settings change
        for w in [self.conf_slider]:
            if isinstance(w, QSlider): w.valueChanged.connect(self._emit_settings_change)
            else: w.currentIndexChanged.connect(self._emit_settings_change)
    
    def update_class_lists(self, class_names):
        self.class_names = class_names

        # 1. "Classes to Detect" group: Default to CHECKED
        detect_layout = self.detect_group.layout()
        while detect_layout.count(): detect_layout.takeAt(0).widget().deleteLater()
        self.class_checkboxes.clear()
        for name in class_names:
            cb = QCheckBox(name)
            # Default to checked, but you can add exceptions like 'background'
            cb.setChecked(name.lower() != 'background')
            cb.stateChanged.connect(self._emit_settings_change)
            detect_layout.addWidget(cb)
            self.class_checkboxes[name] = cb

        # 2. "Good" and "Not Good" groups: Default to UNCHECKED
        for group_box, checkbox_dict in [(self.good_group, self.good_checkboxes), (self.ng_group, self.ng_checkboxes)]:
            layout = group_box.layout()
            while layout.count(): layout.takeAt(0).widget().deleteLater()
            checkbox_dict.clear()
            for name in class_names:
                cb = QCheckBox(name)
                cb.setChecked(False)  # Set to unchecked by default
                cb.stateChanged.connect(self._emit_settings_change)
                layout.addWidget(cb)
                checkbox_dict[name] = cb

        self._emit_settings_change()

    def _emit_settings_change(self):
        # Update line edits from sliders
        self.conf_edit.setText(f"{self.conf_slider.value() / 100.0:.2f}")

        settings = {
            "ConfidenceThreshold": self.conf_slider.value() / 100.0,
            "ClassesToDetect": {name: cb.isChecked() for name, cb in self.class_checkboxes.items()},
            "Good": [name for name, cb in self.good_checkboxes.items() if cb.isChecked()],
            "NotGood": [name for name, cb in self.ng_checkboxes.items() if cb.isChecked()],
        }
        self.settings_changed.emit(settings)
        
    def _create_hbox(self, w1, w2):
        layout = QHBoxLayout()
        layout.addWidget(w1)
        w2.setFixedWidth(50)
        layout.addWidget(w2)
        return layout
    
    def _handle_load_button_clicked(self):
        self.load_btn.setProperty("active_button", "true")
        self.stop_btn.setProperty("active_button", "false")
        self.style().polish(self.load_btn)
        self.style().polish(self.stop_btn)
        self.model_load_requested.emit()
        
    def _handle_stop_button_clicked(self):
        self.stop_btn.setProperty("active_button", "true")
        self.load_btn.setProperty("active_button", "false")
        self.style().polish(self.stop_btn)
        self.style().polish(self.load_btn)
        self.model_stop_requested.emit()
        
    def reset_model_button_states(self):
        self.load_btn.setProperty("active_button", "false")
        self.stop_btn.setProperty("active_button", "false")
        self.style().polish(self.load_btn)
        self.style().polish(self.stop_btn)
        
    def get_settings(self):
        # We save the PATHS, plus the sliders
        return {
            "model_path": self.current_model_path,
            "meta_path": self.current_meta_path,
            "confidence": self.conf_slider.value(),
            "classes_enabled": {name: cb.isChecked() for name, cb in self.class_checkboxes.items()},
            "good_classes": [name for name, cb in self.good_checkboxes.items() if cb.isChecked()],
            "ng_classes": [name for name, cb in self.ng_checkboxes.items() if cb.isChecked()]
        }

    def set_settings(self, settings):
        self.blockSignals(True)
        self.conf_slider.setValue(settings.get("confidence", 50))
        
        # Note: Model Loading happens in MainWindow, which calls this.
        # We just restore the checkboxes here.
        
        # Restore "Detect" checkboxes
        saved_classes = settings.get("classes_enabled", {})
        for name, cb in self.class_checkboxes.items():
            if name in saved_classes:
                cb.setChecked(saved_classes[name])
                
        # Restore Good/NG checkboxes
        good_list = settings.get("good_classes", [])
        ng_list = settings.get("ng_classes", [])
        
        for name, cb in self.good_checkboxes.items():
            cb.setChecked(name in good_list)
        for name, cb in self.ng_checkboxes.items():
            cb.setChecked(name in ng_list)

        self.blockSignals(False)
        self._emit_settings_change()
        
    def reset_ui(self):
        """Resets the UI elements to their empty state."""
        self.class_names = []
        
        # 1. Clear "Classes to Detect" checkboxes
        layout = self.detect_group.layout()
        while layout.count(): 
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.class_checkboxes.clear()

        # 2. Clear "Good" checkboxes
        layout = self.good_group.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.good_checkboxes.clear()

        # 3. Clear "Not Good" checkboxes
        layout = self.ng_group.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()
        self.ng_checkboxes.clear()
        
        # 4. Reset sliders/inputs to defaults (Optional, if desired)
        # self.conf_slider.setValue(50)
        
class TransformPanel(QWidget):
    transform_changed = Signal(dict)
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.rotate_combo = QComboBox()
        self.rotate_combo.addItems(["0", "90", "180", "-90"])
        self.flip_ud_cb = QCheckBox("Flip Up/Down")
        self.flip_lr_cb = QCheckBox("Flip Left/Right")
        form_layout.addRow("Rotation:", self.rotate_combo)
        form_layout.addRow(self.flip_ud_cb)
        form_layout.addRow(self.flip_lr_cb)
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        self.rotate_combo.currentIndexChanged.connect(self._emit_change)
        self.flip_ud_cb.stateChanged.connect(self._emit_change)
        self.flip_lr_cb.stateChanged.connect(self._emit_change)
    def _emit_change(self):
        settings = {'rotate': int(self.rotate_combo.currentText()), 'flip_ud': self.flip_ud_cb.isChecked(), 'flip_lr': self.flip_lr_cb.isChecked()}
        self.transform_changed.emit(settings)
        
    def get_settings(self):
        return {
            "rotate": self.rotate_combo.currentText(),
            "flip_ud": self.flip_ud_cb.isChecked(),
            "flip_lr": self.flip_lr_cb.isChecked()
        }

    def set_settings(self, settings):
        self.blockSignals(True)
        self.rotate_combo.setCurrentText(str(settings.get("rotate", "0")))
        self.flip_ud_cb.setChecked(settings.get("flip_ud", False))
        self.flip_lr_cb.setChecked(settings.get("flip_lr", False))
        self.blockSignals(False)
        self._emit_change()
        
class MediaCapturePanel(QGroupBox):
    capture_image_requested = Signal(str)
    toggle_recording_requested = Signal(str)
    toggle_logging_requested = Signal(str)

    def __init__(self):
        super().__init__("Media Capture (All Feeds)")
        main_layout = QVBoxLayout(self)
        self.folder_edit = QLineEdit("capture_session")
        self.folder_edit.setPlaceholderText("Enter folder name...")
        self.history_list = QListWidget()
        self.capture_img_btn = QPushButton("Capture Image")
        self.record_btn = QPushButton("Start Recording")
        self.log_btn = QPushButton("Start Logging")

        main_layout.addWidget(self.folder_edit)
        main_layout.addWidget(self.history_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.capture_img_btn)
        btn_layout.addWidget(self.record_btn)
        btn_layout.addWidget(self.log_btn)
        main_layout.addLayout(btn_layout)

        self.capture_img_btn.clicked.connect(lambda: self.capture_image_requested.emit(self.folder_edit.text()))
        self.record_btn.clicked.connect(lambda: self.toggle_recording_requested.emit(self.folder_edit.text()))
        self.log_btn.clicked.connect(lambda: self.toggle_logging_requested.emit(self.folder_edit.text()))
        
        # --- NEW: Connect Double Click Signal ---
        self.history_list.itemDoubleClicked.connect(self.open_item_location)

    def add_history(self, message, file_path=None):
        """Adds a message to the list. If file_path is provided, enables double-click to open."""
        item = QListWidgetItem(message)
        if file_path:
            # Store the absolute path in the item's data
            abs_path = os.path.abspath(file_path)
            item.setData(Qt.ItemDataRole.UserRole, abs_path)
            item.setToolTip(f"Double-click to open: {abs_path}")
        self.history_list.insertItem(0, item)

    def open_item_location(self, item):
        """Opens the file or directory stored in the item."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            try:
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", path])
                else:  # Linux
                    subprocess.call(["xdg-open", path])
            except Exception as e:
                print(f"Error opening path: {e}")

    def set_recording_state(self, is_recording): self.record_btn.setText("Stop Recording" if is_recording else "Start Recording")
    def set_logging_state(self, is_logging): self.log_btn.setText("Stop Logging" if is_logging else "Start Logging")
    
class BlobAnalysisPanel(QWidget):
    blob_settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Enable Toggle
        self.enable_cb = QCheckBox("Enable Blob Detection")
        layout.addWidget(self.enable_cb)

        # Tabs for Detail vs Advanced
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- Tab 1: General (Thresholds & Area) ---
        gen_widget = QWidget()
        gen_layout = QFormLayout(gen_widget)
        
        self.min_thresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_thresh_slider.setRange(0, 255); self.min_thresh_slider.setValue(10)
        self.max_thresh_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_thresh_slider.setRange(0, 255); self.max_thresh_slider.setValue(200)
        
        self.min_area_edit = QLineEdit("100")
        self.max_area_edit = QLineEdit("5000")
        
        gen_layout.addRow("Min Threshold:", self._create_label_slider(self.min_thresh_slider))
        gen_layout.addRow("Max Threshold:", self._create_label_slider(self.max_thresh_slider))
        gen_layout.addRow("Min Area (px):", self.min_area_edit)
        gen_layout.addRow("Max Area (px):", self.max_area_edit)
        self.filter_by_area_cb = QCheckBox("Filter By Area"); self.filter_by_area_cb.setChecked(True)
        gen_layout.addRow(self.filter_by_area_cb)
        
        self.tabs.addTab(gen_widget, "General")

        # --- Tab 2: Advanced (Shape & Inertia) ---
        adv_widget = QWidget()
        adv_layout = QFormLayout(adv_widget)

        # Circularity (0.0 to 1.0)
        self.filter_circ_cb = QCheckBox("Filter by Circularity")
        self.min_circ_edit = QLineEdit("0.1")
        adv_layout.addRow(self.filter_circ_cb)
        adv_layout.addRow("Min Circularity:", self.min_circ_edit)

        # Convexity (0.0 to 1.0)
        self.filter_conv_cb = QCheckBox("Filter by Convexity")
        self.min_conv_edit = QLineEdit("0.87")
        adv_layout.addRow(self.filter_conv_cb)
        adv_layout.addRow("Min Convexity:", self.min_conv_edit)

        # Inertia (0.0 to 1.0)
        self.filter_iner_cb = QCheckBox("Filter by Inertia")
        self.min_iner_edit = QLineEdit("0.01")
        adv_layout.addRow(self.filter_iner_cb)
        adv_layout.addRow("Min Inertia Ratio:", self.min_iner_edit)
        
        self.tabs.addTab(adv_widget, "Advanced")

        # --- Color Settings ---
        self.blob_color_combo = QComboBox()
        self.blob_color_combo.addItems(["Dark Blobs (0)", "Light Blobs (255)"])
        adv_layout.addRow("Blob Color:", self.blob_color_combo)

        layout.addStretch()

        self._connect_signals()

    def _create_label_slider(self, slider):
        w = QWidget()
        l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0)
        val_label = QLabel(str(slider.value()))
        val_label.setFixedWidth(30)
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        l.addWidget(slider)
        l.addWidget(val_label)
        return w

    def _connect_signals(self):
        widgets = [
            self.enable_cb, self.min_thresh_slider, self.max_thresh_slider,
            self.min_area_edit, self.max_area_edit, self.filter_by_area_cb,
            self.filter_circ_cb, self.min_circ_edit,
            self.filter_conv_cb, self.min_conv_edit,
            self.filter_iner_cb, self.min_iner_edit, self.blob_color_combo
        ]
        for w in widgets:
            if isinstance(w, QCheckBox): w.stateChanged.connect(self._emit_change)
            elif isinstance(w, QSlider): w.valueChanged.connect(self._emit_change)
            elif isinstance(w, QLineEdit): w.editingFinished.connect(self._emit_change)
            elif isinstance(w, QComboBox): w.currentIndexChanged.connect(self._emit_change)

    def _emit_change(self):
        try:
            settings = {
                "enabled": self.enable_cb.isChecked(),
                "minThreshold": self.min_thresh_slider.value(),
                "maxThreshold": self.max_thresh_slider.value(),
                "filterByArea": self.filter_by_area_cb.isChecked(),
                "minArea": float(self.min_area_edit.text()),
                "maxArea": float(self.max_area_edit.text()),
                "filterByCircularity": self.filter_circ_cb.isChecked(),
                "minCircularity": float(self.min_circ_edit.text()),
                "filterByConvexity": self.filter_conv_cb.isChecked(),
                "minConvexity": float(self.min_conv_edit.text()),
                "filterByInertia": self.filter_iner_cb.isChecked(),
                "minInertiaRatio": float(self.min_iner_edit.text()),
                "blobColor": 0 if "Dark" in self.blob_color_combo.currentText() else 255
            }
            self.blob_settings_changed.emit(settings)
        except ValueError:
            pass # Handle invalid float inputs gracefully

    def get_settings(self):
        # Trigger an emit to capture current state easily or reconstruct manually
        # For brevity, re-using emit logic structure:
        self._emit_change() 
        # Ideally, return the dict directly:
        return {
            "enabled": self.enable_cb.isChecked(),
            "minThreshold": self.min_thresh_slider.value(),
            "maxThreshold": self.max_thresh_slider.value(),
            "filterByArea": self.filter_by_area_cb.isChecked(),
            "minArea": self.min_area_edit.text(),
            "maxArea": self.max_area_edit.text(),
            "filterByCircularity": self.filter_circ_cb.isChecked(),
            "minCircularity": self.min_circ_edit.text(),
            "filterByConvexity": self.filter_conv_cb.isChecked(),
            "minConvexity": self.min_conv_edit.text(),
            "filterByInertia": self.filter_iner_cb.isChecked(),
            "minInertiaRatio": self.min_iner_edit.text(),
            "blobColor": self.blob_color_combo.currentText()
        }

    def set_settings(self, s):
        self.blockSignals(True)
        self.enable_cb.setChecked(s.get("enabled", False))
        self.min_thresh_slider.setValue(s.get("minThreshold", 10))
        self.max_thresh_slider.setValue(s.get("maxThreshold", 200))
        self.filter_by_area_cb.setChecked(s.get("filterByArea", True))
        self.min_area_edit.setText(str(s.get("minArea", 100)))
        self.max_area_edit.setText(str(s.get("maxArea", 5000)))
        self.filter_circ_cb.setChecked(s.get("filterByCircularity", False))
        self.min_circ_edit.setText(str(s.get("minCircularity", 0.1)))
        self.filter_conv_cb.setChecked(s.get("filterByConvexity", False))
        self.min_conv_edit.setText(str(s.get("minConvexity", 0.87)))
        self.filter_iner_cb.setChecked(s.get("filterByInertia", False))
        self.min_iner_edit.setText(str(s.get("minInertiaRatio", 0.01)))
        self.blob_color_combo.setCurrentText(s.get("blobColor", "Dark Blobs (0)"))
        self.blockSignals(False)
        self._emit_change()
        
        
class Measurement:
    def __init__(self, type_str, params, is_active=True):
        self.type = type_str  # 'Circle', 'Rectangle', 'Complex'
        self.params = params  # Dict of parameters (e.g., {'min_radius': 10, 'max_radius': 100})
        self.is_active = is_active
        self.results = {}     # Dict to store latest results

class EdgeDetectionPanel(QWidget):
    edge_settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ==========================================
        # 1. MASTER TOGGLE
        # ==========================================
        self.enable_cb = QCheckBox("Enable Edge Detection")
        self.enable_cb.setStyleSheet("font-weight: bold; font-size: 11pt;")
        main_layout.addWidget(self.enable_cb)

        # Container for all edge settings (Hidden if Master Toggle is False)
        self.edge_settings_container = QWidget()
        edge_container_layout = QVBoxLayout(self.edge_settings_container)
        edge_container_layout.setContentsMargins(0, 5, 0, 0)
        main_layout.addWidget(self.edge_settings_container)

        # ==========================================
        # 2. EDGE TYPE SELECTION
        # ==========================================
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Algorithm:"))
        self.edge_type_combo = QComboBox()
        self.edge_type_combo.addItems(["Canny", "Sobel (Gradient)", "Laplacian"])
        type_layout.addWidget(self.edge_type_combo)
        edge_container_layout.addLayout(type_layout)

        # ==========================================
        # 3. DYNAMIC PARAMETER STACK
        # ==========================================
        # We use a StackedWidget to show ONLY the sliders relevant to the selected mode
        self.param_stack = QStackedWidget()
        edge_container_layout.addWidget(self.param_stack)

        # --- PAGE 0: Canny Parameters ---
        canny_page = QWidget()
        canny_layout = QFormLayout(canny_page)
        self.canny_t1_slider = QSlider(Qt.Orientation.Horizontal); self.canny_t1_slider.setRange(0, 255); self.canny_t1_slider.setValue(50)
        self.canny_t2_slider = QSlider(Qt.Orientation.Horizontal); self.canny_t2_slider.setRange(0, 255); self.canny_t2_slider.setValue(150)
        canny_layout.addRow("Threshold 1:", self._create_label_slider(self.canny_t1_slider))
        canny_layout.addRow("Threshold 2:", self._create_label_slider(self.canny_t2_slider))
        self.param_stack.addWidget(canny_page)

        # --- PAGE 1: Sobel Parameters ---
        sobel_page = QWidget()
        sobel_layout = QFormLayout(sobel_page)
        self.sobel_k_slider = QSlider(Qt.Orientation.Horizontal)
        # Sobel k-size must be 1, 3, 5, or 7
        self.sobel_k_slider.setRange(1, 7); self.sobel_k_slider.setValue(3); self.sobel_k_slider.setSingleStep(2)
        sobel_layout.addRow("Kernel Size (Odd):", self._create_label_slider(self.sobel_k_slider))
        self.param_stack.addWidget(sobel_page)

        # --- PAGE 2: Laplacian Parameters ---
        laplace_page = QWidget()
        laplace_layout = QFormLayout(laplace_page)
        self.laplace_k_slider = QSlider(Qt.Orientation.Horizontal)
        # Laplacian k-size must be odd
        self.laplace_k_slider.setRange(1, 7); self.laplace_k_slider.setValue(3); self.laplace_k_slider.setSingleStep(2)
        laplace_layout.addRow("Kernel Size (Odd):", self._create_label_slider(self.laplace_k_slider))
        self.param_stack.addWidget(laplace_page)

        # Separator
        edge_container_layout.addWidget(self._create_line())

        # ==========================================
        # 4. DEFECT DETECTION (Collapsible)
        # ==========================================
        self.defect_enable_cb = QCheckBox("Highlight Defects (Pinholes/Spots)")
        edge_container_layout.addWidget(self.defect_enable_cb)

        self.defect_container = QWidget()
        defect_layout = QFormLayout(self.defect_container)
        defect_layout.setContentsMargins(10, 0, 0, 0) # Indent slightly

        self.defect_blur_slider = QSlider(Qt.Orientation.Horizontal); self.defect_blur_slider.setRange(1, 15); self.defect_blur_slider.setValue(5); self.defect_blur_slider.setSingleStep(2)
        self.defect_thresh_slider = QSlider(Qt.Orientation.Horizontal); self.defect_thresh_slider.setRange(1, 255); self.defect_thresh_slider.setValue(25)
        self.defect_min_area_edit = QLineEdit("20")
        self.defect_max_area_edit = QLineEdit("100000")

        defect_layout.addRow("Blur (Noise Removal):", self._create_label_slider(self.defect_blur_slider))
        defect_layout.addRow("Sensitivity Thresh:", self._create_label_slider(self.defect_thresh_slider))
        defect_layout.addRow("Min Area:", self.defect_min_area_edit)
        defect_layout.addRow("Max Area:", self.defect_max_area_edit)
        
        edge_container_layout.addWidget(self.defect_container)
        edge_container_layout.addWidget(self._create_line())

        # ==========================================
        # 5. MORPHOLOGY (Collapsible)
        # ==========================================
        self.morph_enable_cb = QCheckBox("Enable Morphology (Cleanup)")
        edge_container_layout.addWidget(self.morph_enable_cb)

        self.morph_container = QWidget()
        morph_layout = QFormLayout(self.morph_container)
        morph_layout.setContentsMargins(10, 0, 0, 0) # Indent

        self.morph_op_combo = QComboBox()
        self.morph_op_combo.addItems(["DILATE", "ERODE", "OPEN", "CLOSE"])
        self.morph_kernel_size_slider = QSlider(Qt.Orientation.Horizontal); self.morph_kernel_size_slider.setRange(1, 15); self.morph_kernel_size_slider.setValue(3)
        self.morph_iterations_slider = QSlider(Qt.Orientation.Horizontal); self.morph_iterations_slider.setRange(1, 5); self.morph_iterations_slider.setValue(1)

        morph_layout.addRow("Operation:", self.morph_op_combo)
        morph_layout.addRow("Kernel Size:", self._create_label_slider(self.morph_kernel_size_slider))
        morph_layout.addRow("Iterations:", self._create_label_slider(self.morph_iterations_slider))

        edge_container_layout.addWidget(self.morph_container)
        
        main_layout.addStretch()

        # ==========================================
        # LOGIC & CONNECTIONS
        # ==========================================
        self._connect_signals()
        
        # Initial Visibility State
        self.update_visibility()

    def _create_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _create_label_slider(self, slider):
        w = QWidget()
        l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0)
        val_label = QLabel(str(slider.value()))
        val_label.setFixedWidth(30)
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        l.addWidget(slider)
        l.addWidget(val_label)
        return w

    def update_visibility(self):
        # 1. Master Toggle
        self.edge_settings_container.setVisible(self.enable_cb.isChecked())
        
        # 2. Defect Toggle
        self.defect_container.setVisible(self.defect_enable_cb.isChecked())
        
        # 3. Morph Toggle
        self.morph_container.setVisible(self.morph_enable_cb.isChecked())

        # 4. Stack Page (Canny vs Sobel vs Laplace)
        # Index matches the order added to addItems(["Canny", "Sobel", "Laplacian"])
        self.param_stack.setCurrentIndex(self.edge_type_combo.currentIndex())

    def _connect_signals(self):
        # Visibility Triggers
        self.enable_cb.toggled.connect(self.update_visibility)
        self.defect_enable_cb.toggled.connect(self.update_visibility)
        self.morph_enable_cb.toggled.connect(self.update_visibility)
        self.edge_type_combo.currentIndexChanged.connect(self.update_visibility)
        
        # Emit Settings Triggers
        widgets = [
            self.enable_cb, self.edge_type_combo,
            self.canny_t1_slider, self.canny_t2_slider,
            self.sobel_k_slider, self.laplace_k_slider, # New Sliders
            self.defect_enable_cb, self.defect_blur_slider, self.defect_thresh_slider, 
            self.defect_min_area_edit, self.defect_max_area_edit,
            self.morph_enable_cb, self.morph_op_combo, 
            self.morph_kernel_size_slider, self.morph_iterations_slider
        ]
        
        for w in widgets:
            if isinstance(w, QCheckBox): w.stateChanged.connect(self._emit_change)
            elif isinstance(w, QSlider): w.valueChanged.connect(self._emit_change)
            elif isinstance(w, QComboBox): w.currentIndexChanged.connect(self._emit_change)
            elif isinstance(w, QLineEdit): w.editingFinished.connect(self._emit_change)

    def _emit_change(self):
        # Validation for odd numbers on kernels
        for slider in [self.defect_blur_slider, self.sobel_k_slider, self.laplace_k_slider]:
            val = slider.value()
            if val % 2 == 0: val += 1 # Force odd
        
        try: min_area = float(self.defect_min_area_edit.text())
        except: min_area = 20.0
            
        try: max_area = float(self.defect_max_area_edit.text())
        except: max_area = 100000.0

        settings = {
            "enabled": self.enable_cb.isChecked(),
            "edge_type": self.edge_type_combo.currentText(),
            
            # Canny
            "canny_t1": self.canny_t1_slider.value(),
            "canny_t2": self.canny_t2_slider.value(),
            
            # Sobel / Laplace
            "sobel_k": self.sobel_k_slider.value() if self.sobel_k_slider.value() % 2 != 0 else self.sobel_k_slider.value() + 1,
            "laplace_k": self.laplace_k_slider.value() if self.laplace_k_slider.value() % 2 != 0 else self.laplace_k_slider.value() + 1,

            # Defect
            "defect_enabled": self.defect_enable_cb.isChecked(),
            "defect_blur": self.defect_blur_slider.value() if self.defect_blur_slider.value() % 2 != 0 else self.defect_blur_slider.value() + 1,
            "defect_thresh": self.defect_thresh_slider.value(),
            "defect_min_area": min_area,
            "defect_max_area": max_area,
            
            # Morphology
            "morph_enabled": self.morph_enable_cb.isChecked(),
            "morph_op": self.morph_op_combo.currentText(),
            "morph_kernel": self.morph_kernel_size_slider.value(),
            "morph_iter": self.morph_iterations_slider.value()
        }
        self.edge_settings_changed.emit(settings)
        
    def get_settings(self):
        # (Same logic as _emit_change, just returning the dict)
        try: min_area = float(self.defect_min_area_edit.text())
        except: min_area = 20.0
        try: max_area = float(self.defect_max_area_edit.text())
        except: max_area = 100000.0
            
        return {
            "enabled": self.enable_cb.isChecked(),
            "edge_type": self.edge_type_combo.currentText(),
            "canny_t1": self.canny_t1_slider.value(),
            "canny_t2": self.canny_t2_slider.value(),
            "sobel_k": self.sobel_k_slider.value(),
            "laplace_k": self.laplace_k_slider.value(),
            "morph_enabled": self.morph_enable_cb.isChecked(),
            "morph_op": self.morph_op_combo.currentText(),
            "morph_kernel": self.morph_kernel_size_slider.value(),
            "morph_iter": self.morph_iterations_slider.value(),
            "defect_enabled": self.defect_enable_cb.isChecked(),
            "defect_threshold": self.defect_thresh_slider.value(),
            "defect_blur": self.defect_blur_slider.value(),
            "defect_min_area": min_area,
            "defect_max_area": max_area
        }

    def set_settings(self, s):
        self.blockSignals(True)
        self.enable_cb.setChecked(s.get("enabled", False))
        self.edge_type_combo.setCurrentText(s.get("edge_type", "Canny"))
        
        self.canny_t1_slider.setValue(s.get("canny_t1", 50))
        self.canny_t2_slider.setValue(s.get("canny_t2", 150))
        self.sobel_k_slider.setValue(s.get("sobel_k", 3))
        self.laplace_k_slider.setValue(s.get("laplace_k", 3))
        
        self.defect_enable_cb.setChecked(s.get("defect_enabled", False))
        self.defect_blur_slider.setValue(s.get("defect_blur", 5))
        self.defect_thresh_slider.setValue(s.get("defect_threshold", 25))
        self.defect_min_area_edit.setText(str(s.get("defect_min_area", 20.0)))
        self.defect_max_area_edit.setText(str(s.get("defect_max_area", 100000.0)))

        self.morph_enable_cb.setChecked(s.get("morph_enabled", False))
        self.morph_op_combo.setCurrentText(s.get("morph_op", "DILATE"))
        self.morph_kernel_size_slider.setValue(s.get("morph_kernel", 3))
        self.morph_iterations_slider.setValue(s.get("morph_iter", 1))
        
        self.blockSignals(False)
        self.update_visibility() # Ensure UI state matches loaded data
        self._emit_change()

class MetrologyPanel(QWidget):
    metrology_settings_changed = Signal(list)
    manual_mode_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)

        # --- Manual Measurement Group ---
        manual_group = QGroupBox("Manual Measurement")
        manual_layout = QHBoxLayout(manual_group)
        
        self.manual_area_cb = QCheckBox("Area")
        self.manual_length_cb = QCheckBox("Length")
        
        # Enforce exclusivity (Like Radio Buttons but uncheckable)
        self.manual_area_cb.clicked.connect(self._on_area_clicked)
        self.manual_length_cb.clicked.connect(self._on_length_clicked)
        
        manual_layout.addWidget(self.manual_area_cb)
        manual_layout.addWidget(self.manual_length_cb)
        main_layout.addWidget(manual_group)

        # --- Measurement List and Controls ---
        
        title_lbl = QLabel("<b>Measurement/Metrology Setup</b>")
        title_lbl.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(title_lbl)
        
        self.measurement_list = QListWidget()
        main_layout.addWidget(self.measurement_list)

        btn_layout = QHBoxLayout()
        self.add_circle_btn = QPushButton("Add Circle")
        self.add_rect_btn = QPushButton("Add Rectangle")
        self.add_complex_btn = QPushButton("Add Complex")
        self.remove_btn = QPushButton("Remove Selected")
        btn_layout.addWidget(self.add_circle_btn)
        btn_layout.addWidget(self.add_rect_btn)
        btn_layout.addWidget(self.add_complex_btn)
        btn_layout.addWidget(self.remove_btn)
        main_layout.addLayout(btn_layout)
        
        # --- Results Display ---
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(100)
        main_layout.addWidget(QLabel("<b>Latest Results:</b>"))
        main_layout.addWidget(self.results_list)

        self.measurements = []
        self._connect_signals()

    def _on_area_clicked(self, checked):
        if checked:
            self.manual_length_cb.setChecked(False)
            self.manual_mode_changed.emit("Area")
        else:
            self.manual_mode_changed.emit(None)

    def _on_length_clicked(self, checked):
        if checked:
            self.manual_area_cb.setChecked(False)
            self.manual_mode_changed.emit("Length")
        else:
            self.manual_mode_changed.emit(None)

    def _connect_signals(self):
        self.add_circle_btn.clicked.connect(lambda: self._add_measurement('Circle'))
        self.add_rect_btn.clicked.connect(lambda: self._add_measurement('Rectangle'))
        self.add_complex_btn.clicked.connect(lambda: self._add_measurement('Complex'))
        self.remove_btn.clicked.connect(self._remove_measurement)
        self.measurement_list.itemChanged.connect(self._emit_change)
        
    def _add_measurement(self, type_str):
        # Default Parameters based on type
        params = {}
        if type_str == 'Circle':
            params = {'min_radius': 10, 'max_radius': 100, 'min_dist': 50}
        elif type_str == 'Rectangle':
            params = {'approx_thresh': 0.04, 'aspect_ratio_tol': 0.2}
        elif type_str == 'Complex':
            params = {'min_area': 1000, 'min_verticies': 4}
            
        new_item = Measurement(type_str, params)
        self.measurements.append(new_item)
        
        # Add to ListWidget
        list_item = QListWidgetItem(f"{type_str} {len(self.measurements)} (Active)", self.measurement_list)
        list_item.setData(Qt.ItemDataRole.UserRole, new_item)
        list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        list_item.setCheckState(Qt.CheckState.Checked)
        
        self.metrology_settings_changed.emit(self.measurements)

    def _remove_measurement(self):
        selected_items = self.measurement_list.selectedItems()
        if not selected_items: return
        
        for item in selected_items:
            # Remove from internal list
            measurement_obj = item.data(Qt.ItemDataRole.UserRole)
            if measurement_obj in self.measurements:
                self.measurements.remove(measurement_obj)
            # Remove from UI
            self.measurement_list.takeItem(self.measurement_list.row(item))
            
        self._emit_change()

    def _emit_change(self):
        # Update active/inactive state from checkboxes
        for i in range(self.measurement_list.count()):
            item = self.measurement_list.item(i)
            measurement_obj = item.data(Qt.ItemDataRole.UserRole)

            if measurement_obj is None:
                continue

            measurement_obj.is_active = (item.checkState() == Qt.CheckState.Checked)
            
        # Re-emit the internal list for the thread
        self.metrology_settings_changed.emit(self.measurements)

    def update_results(self, serial, results_list):
        # This method is called by the MainWindow when a frame is ready
        self.results_list.clear()
        if not results_list:
            self.results_list.addItem(f"No active measurements for {serial} or no shapes found.")
            return

        for result in results_list:
            result_str = f"[{result['type']}] {result.get('status', 'OK')} - "
            for k, v in result['metrics'].items():
                result_str += f"{k}: {v:.2f}, "
            self.results_list.addItem(result_str.rstrip(', '))

    def get_settings(self):
        # Convert internal list of Measurement objects to a serializable list of dicts
        serializable_list = []
        for m in self.measurements:
            serializable_list.append({
                'type': m.type,
                'params': m.params,
                'is_active': m.is_active
            })
        return serializable_list

    def set_settings(self, settings_list):
        self.blockSignals(True)
        self.measurement_list.clear()
        self.measurements.clear()
        
        for s in settings_list:
            m = Measurement(s['type'], s['params'], s['is_active'])
            self.measurements.append(m)
            
            list_item = QListWidgetItem(f"{m.type} {len(self.measurements)} ({'Active' if m.is_active else 'Inactive'})", self.measurement_list)
            list_item.setData(Qt.ItemDataRole.UserRole, m)
            list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            list_item.setCheckState(Qt.CheckState.Checked if m.is_active else Qt.CheckState.Unchecked)

        self.blockSignals(False)
        self._emit_change() # Emit the restored list
        
class ConveyorTriggerPanel(QWidget):
    trigger_settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.enable_cb = QCheckBox("Enable Conveyor Trigger")
        
        # Zone Definition (Percent of screen)
        self.x_slider = QSlider(Qt.Orientation.Horizontal)
        self.x_slider.setRange(0, 100); self.x_slider.setValue(40)
        
        self.y_slider = QSlider(Qt.Orientation.Horizontal)
        self.y_slider.setRange(0, 100); self.y_slider.setValue(40)
        
        self.w_slider = QSlider(Qt.Orientation.Horizontal)
        self.w_slider.setRange(1, 100); self.w_slider.setValue(20)
        
        self.h_slider = QSlider(Qt.Orientation.Horizontal)
        self.h_slider.setRange(1, 100); self.h_slider.setValue(20)
        
        # Cooldown (Seconds between captures)
        self.cooldown_edit = QLineEdit("0")
        
        # Folder Name for auto-captures
        self.folder_edit = QLineEdit("conveyor_captures")
        
        form_layout.addRow(self.enable_cb)
        form_layout.addRow("Zone X (%)", self._create_label_slider(self.x_slider))
        form_layout.addRow("Zone Y (%)", self._create_label_slider(self.y_slider))
        form_layout.addRow("Zone Width (%)", self._create_label_slider(self.w_slider))
        form_layout.addRow("Zone Height (%)", self._create_label_slider(self.h_slider))
        form_layout.addRow("Cooldown (sec):", self.cooldown_edit)
        form_layout.addRow("Save Folder:", self.folder_edit)
        
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        
        self._connect_signals()

    def _create_label_slider(self, slider):
        w = QWidget()
        l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0)
        val_label = QLabel(str(slider.value()))
        val_label.setFixedWidth(30)
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        l.addWidget(slider)
        l.addWidget(val_label)
        return w

    def _connect_signals(self):
        for w in [self.enable_cb, self.x_slider, self.y_slider, self.w_slider, self.h_slider]:
            if isinstance(w, QCheckBox): w.stateChanged.connect(self._emit_change)
            else: w.valueChanged.connect(self._emit_change)
        self.cooldown_edit.editingFinished.connect(self._emit_change)
        self.folder_edit.editingFinished.connect(self._emit_change)

    def _emit_change(self):
        try:
            cooldown = float(self.cooldown_edit.text())
        except:
            cooldown = 2.0
            
        settings = {
            "enabled": self.enable_cb.isChecked(),
            "x_pct": self.x_slider.value() / 100.0,
            "y_pct": self.y_slider.value() / 100.0,
            "w_pct": self.w_slider.value() / 100.0,
            "h_pct": self.h_slider.value() / 100.0,
            "cooldown": cooldown,
            "folder": self.folder_edit.text()
        }
        self.trigger_settings_changed.emit(settings)

    def get_settings(self):
        self._emit_change() # Ensure current state is captured
        return {
            "enabled": self.enable_cb.isChecked(),
            "x_pct": self.x_slider.value(),
            "y_pct": self.y_slider.value(),
            "w_pct": self.w_slider.value(),
            "h_pct": self.h_slider.value(),
            "cooldown": self.cooldown_edit.text(),
            "folder": self.folder_edit.text()
        }

    def set_settings(self, s):
        self.blockSignals(True)
        self.enable_cb.setChecked(s.get("enabled", False))
        self.x_slider.setValue(s.get("x_pct", 40))
        self.y_slider.setValue(s.get("y_pct", 40))
        self.w_slider.setValue(s.get("w_pct", 20))
        self.h_slider.setValue(s.get("h_pct", 20))
        self.cooldown_edit.setText(str(s.get("cooldown", "2.0")))
        self.folder_edit.setText(s.get("folder", "conveyor_captures"))
        self.blockSignals(False)
        self._emit_change()


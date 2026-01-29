"""
This module contains napari widgets for Fourier transform analysis.
"""

from typing import TYPE_CHECKING

import numpy as np
from magicgui.widgets import create_widget
from qtpy.QtCore import Qt, QRect, QPoint, QPointF
from qtpy.QtGui import QPainter, QPen, QImage, QPixmap
from qtpy.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QLabel,
)

if TYPE_CHECKING:
    import napari
else:
    import napari.layers


class FTImageLabel(QLabel):
    """Custom QLabel for displaying FT image with proper mouse coordinate handling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap = None
        self._zoom_level = 1.0
        self._pan_offset = QPoint(0, 0)
        self._full_image_size = None  # Size of full unzoomed image

    def setPixmap(self, pixmap):
        """Store original pixmap and update display"""
        self._original_pixmap = pixmap
        super().setPixmap(pixmap)

    def set_zoom_params(self, zoom_level, pan_offset, full_image_size):
        """Update zoom and pan parameters for coordinate transformation"""
        self._zoom_level = zoom_level
        self._pan_offset = pan_offset
        self._full_image_size = full_image_size

    def get_image_coordinates(self, pos):
        """Convert widget coordinates to original (full, unzoomed) image coordinates"""
        if self._original_pixmap is None or self._original_pixmap.isNull():
            return None
        if self._full_image_size is None:
            return None

        # Get the displayed (zoomed/cropped) pixmap dimensions
        display_pixmap_width = self._original_pixmap.width()
        display_pixmap_height = self._original_pixmap.height()

        # Get the widget dimensions
        widget_width = self.width()
        widget_height = self.height()

        # Calculate scaling factor for displaying pixmap in widget (maintaining aspect ratio)
        scale = min(
            widget_width / display_pixmap_width,
            widget_height / display_pixmap_height,
        )

        # Calculate the actual displayed size
        display_width = display_pixmap_width * scale
        display_height = display_pixmap_height * scale

        # Calculate offset (image is centered)
        offset_x = (widget_width - display_width) / 2
        offset_y = (widget_height - display_height) / 2

        # Convert widget coordinates to displayed pixmap coordinates
        pixmap_x = (pos.x() - offset_x) / scale
        pixmap_y = (pos.y() - offset_y) / scale

        # Check if click is within displayed pixmap bounds
        if (
            pixmap_x < 0
            or pixmap_x >= display_pixmap_width
            or pixmap_y < 0
            or pixmap_y >= display_pixmap_height
        ):
            return None

        # Convert from displayed (zoomed view) coordinates to full image coordinates
        # The displayed pixmap shows a zoomed/cropped portion of the full image
        full_img_x = (pixmap_x / self._zoom_level) + self._pan_offset.x()
        full_img_y = (pixmap_y / self._zoom_level) + self._pan_offset.y()

        # Check if within full image bounds
        if (
            full_img_x < 0
            or full_img_x >= self._full_image_size[0]
            or full_img_y < 0
            or full_img_y >= self._full_image_size[1]
        ):
            return None

        return QPoint(int(full_img_x), int(full_img_y))


class FourierTransformWidget(QWidget):
    """
    Interactive Fourier Transform filtering widget.

    Allows users to:
    - Select a 2D image from the viewer
    - View its FFT-shifted Fourier transform
    - Draw boxes on the FT to create masks
    - Apply inverse FFT with masking to create filtered images
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer

        # State variables
        self.current_image_layer = None
        self.ft_data = None  # Complex FFT data
        self.ft_display = None  # Log magnitude for display
        self.boxes = []  # List of QRect objects (inclusion boxes)
        self.anti_boxes = []  # List of QRect objects (exclusion boxes)
        self.drawing = False
        self.drawing_anti = False  # True when drawing an anti-box
        self.start_point = None
        self.current_rect = None
        self.filtered_layer_name = None
        self.base_pixmap = None  # Cached base pixmap without current box

        # Zoom and pan state
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)  # Pan offset in image coordinates
        self.panning = False
        self.pan_start = None

        # Shape mode: 'rectangle' or 'circle'
        self.shape_mode = "rectangle"

        # Setup UI
        self._setup_ui()

        # Connect to viewer layer events to keep combo updated
        self.viewer.layers.events.inserted.connect(self._on_layers_changed)
        self.viewer.layers.events.removed.connect(self._on_layers_changed)

        # If there's already an image layer selected, compute FFT
        if self.image_combo.value is not None:
            self._on_image_selected()

    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout()

        # Image layer selection
        # Pass viewer context so magicgui can find layers
        self.image_combo = create_widget(
            label="Image Layer",
            annotation="napari.layers.Image",
            options={"choices": self._get_image_layers},
        )
        self.image_combo.changed.connect(self._on_image_selected)
        layout.addWidget(self.image_combo.native)

        # FT Display label - use custom label with proper coordinate handling
        self.ft_label = FTImageLabel()
        self.ft_label.setMinimumSize(400, 400)
        self.ft_label.setMaximumSize(600, 600)
        self.ft_label.setScaledContents(
            False
        )  # Don't auto-scale, we'll handle it
        self.ft_label.setAlignment(Qt.AlignCenter)  # Center the image
        self.ft_label.setStyleSheet("border: 1px solid black;")
        self.ft_label.setMouseTracking(True)
        self.ft_label.mousePressEvent = self._on_mouse_press
        self.ft_label.mouseMoveEvent = self._on_mouse_move
        self.ft_label.mouseReleaseEvent = self._on_mouse_release
        self.ft_label.wheelEvent = self._on_mouse_wheel
        layout.addWidget(self.ft_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.shape_button = QPushButton("Shape: Rectangle")
        self.shape_button.clicked.connect(self._toggle_shape)
        button_layout.addWidget(self.shape_button)

        self.reset_boxes_button = QPushButton("Reset Boxes")
        self.reset_boxes_button.clicked.connect(self._reset_boxes)
        button_layout.addWidget(self.reset_boxes_button)

        self.reset_view_button = QPushButton("Reset View")
        self.reset_view_button.clicked.connect(self._reset_view)
        button_layout.addWidget(self.reset_view_button)

        layout.addLayout(button_layout)

        # Info label
        self.info_label = QLabel("Select an image layer to begin")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def _get_image_layers(self, widget):
        """Get list of image layers from viewer"""
        return [
            layer
            for layer in self.viewer.layers
            if isinstance(layer, napari.layers.Image)
        ]

    def _on_layers_changed(self, event):
        """Handle when layers are added or removed from viewer"""
        # Reset the choices to update the combo box
        self.image_combo.reset_choices()

    def _toggle_shape(self):
        """Toggle between rectangle and circle shape modes"""
        if self.shape_mode == "rectangle":
            self.shape_mode = "circle"
            self.shape_button.setText("Shape: Circle")
        else:
            self.shape_mode = "rectangle"
            self.shape_button.setText("Shape: Rectangle")

    def _on_image_selected(self):
        """Handle image layer selection"""
        # Disconnect from previous layer if any
        if self.current_image_layer is not None:
            self.current_image_layer.events.data.disconnect(
                self._on_layer_data_changed
            )
            self.current_image_layer.events.scale.disconnect(
                self._on_layer_scale_changed
            )

        self.current_image_layer = self.image_combo.value

        # Reset state when changing images
        self.boxes = []
        self.anti_boxes = []
        self.current_rect = None
        self.filtered_layer_name = None
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)

        if self.current_image_layer is None:
            self.info_label.setText("No image selected")
            self.ft_label.clear()
            self.ft_data = None
            self.ft_display = None
            return

        # Connect to layer data and scale changes
        self.current_image_layer.events.data.connect(
            self._on_layer_data_changed
        )
        self.current_image_layer.events.scale.connect(
            self._on_layer_scale_changed
        )

        # Get the image data
        image_data = self.current_image_layer.data

        # Check if it's 2D
        if image_data.ndim != 2:
            self.info_label.setText("Please select a 2D image")
            self.ft_label.clear()
            self.ft_data = None
            self.ft_display = None
            return

        # Compute FFT
        self._compute_fft(image_data)
        self._update_display()
        self.info_label.setText(
            "Draw boxes on the Fourier transform to filter"
        )

    def _on_layer_data_changed(self, event):
        """Handle when the layer data changes"""
        if self.current_image_layer is None:
            return

        image_data = self.current_image_layer.data

        # Check if it's still 2D
        if image_data.ndim != 2:
            self.info_label.setText("Please select a 2D image")
            self.ft_label.clear()
            self.ft_data = None
            self.ft_display = None
            return

        # Recompute FFT with new data
        self._compute_fft(image_data)
        self._update_display()

        # If there's a filtered layer, update it
        if self.filtered_layer_name is not None and len(self.boxes) > 0:
            self._apply_filter()

    def _on_layer_scale_changed(self, event):
        """Handle when the parent layer scale changes"""
        if self.current_image_layer is None:
            return

        # Update the filtered layer scale to match parent
        if self.filtered_layer_name is not None:
            if self.filtered_layer_name in self.viewer.layers:
                filtered_layer = self.viewer.layers[self.filtered_layer_name]
                filtered_layer.scale = self.current_image_layer.scale

    def _compute_fft(self, image_data):
        """Compute the FFT-shifted Fourier transform"""
        # Compute FFT and shift
        ft = np.fft.fft2(image_data)
        self.ft_data = np.fft.fftshift(ft)

        # Compute log magnitude for display
        magnitude = np.abs(self.ft_data)
        # Add small epsilon to avoid log(0)
        self.ft_display = np.log(magnitude + 1e-10)

    def _update_display(self, fast_redraw=False):
        """Update the FT display with boxes

        Args:
            fast_redraw: If True, only redraw boxes on cached base pixmap (fast)
                        If False, regenerate entire display from FT data (slow)
        """
        if self.ft_display is None:
            return

        if not fast_redraw:
            # Full regeneration - normalize and convert FT display to pixmap
            display_normalized = self.ft_display - self.ft_display.min()
            display_normalized = display_normalized / (
                display_normalized.max() + 1e-10
            )
            display_normalized = (display_normalized * 255).astype(np.uint8)

            # Get full image dimensions
            full_height, full_width = display_normalized.shape

            # Calculate the visible region based on zoom and pan
            # Visible region size in original image coordinates
            visible_width = full_width / self.zoom_level
            visible_height = full_height / self.zoom_level

            # Calculate crop boundaries
            x1 = int(max(0, self.pan_offset.x()))
            y1 = int(max(0, self.pan_offset.y()))
            x2 = int(min(full_width, self.pan_offset.x() + visible_width))
            y2 = int(min(full_height, self.pan_offset.y() + visible_height))

            # Crop the visible region and make contiguous
            cropped = display_normalized[y1:y2, x1:x2].copy()

            # Convert to QImage
            crop_height, crop_width = cropped.shape
            bytes_per_line = crop_width
            q_image = QImage(
                cropped.data,
                crop_width,
                crop_height,
                bytes_per_line,
                QImage.Format_Grayscale8,
            )

            # Convert to pixmap
            self.base_pixmap = QPixmap.fromImage(q_image)

            # Scale up if zoomed (make zoomed view appear larger)
            if self.zoom_level > 1.0:
                scaled_size = self.base_pixmap.size() * self.zoom_level
                self.base_pixmap = self.base_pixmap.scaled(
                    scaled_size, Qt.KeepAspectRatio, Qt.FastTransformation
                )

            # Draw completed boxes in the zoomed coordinate system
            painter = QPainter(self.base_pixmap)

            # Draw inclusion boxes in red
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            for box in self.boxes:
                # Transform box from full image coords to zoomed view coords
                transformed_box = self._transform_box_to_view(box)
                if transformed_box is not None:
                    if hasattr(box, "is_circle") and box.is_circle:
                        # For circles, draw using center and radius from diameter
                        center_x = (
                            transformed_box.left() + transformed_box.right()
                        ) / 2
                        center_y = (
                            transformed_box.top() + transformed_box.bottom()
                        ) / 2
                        dx = transformed_box.right() - transformed_box.left()
                        dy = transformed_box.bottom() - transformed_box.top()
                        radius = np.sqrt(dx**2 + dy**2) / 2
                        painter.drawEllipse(
                            QPointF(center_x, center_y), radius, radius
                        )
                    else:
                        painter.drawRect(transformed_box)

            # Draw exclusion boxes (anti-boxes) in blue
            pen_anti = QPen(Qt.blue, 2)
            painter.setPen(pen_anti)
            for box in self.anti_boxes:
                transformed_box = self._transform_box_to_view(box)
                if transformed_box is not None:
                    if hasattr(box, "is_circle") and box.is_circle:
                        # For circles, draw using center and radius from diameter
                        center_x = (
                            transformed_box.left() + transformed_box.right()
                        ) / 2
                        center_y = (
                            transformed_box.top() + transformed_box.bottom()
                        ) / 2
                        dx = transformed_box.right() - transformed_box.left()
                        dy = transformed_box.bottom() - transformed_box.top()
                        radius = np.sqrt(dx**2 + dy**2) / 2
                        painter.drawEllipse(
                            QPointF(center_x, center_y), radius, radius
                        )
                    else:
                        painter.drawRect(transformed_box)

            painter.end()  # Create a copy of base pixmap for drawing current box
        if self.base_pixmap is None:
            return

        pixmap = self.base_pixmap.copy()

        # Draw current box being drawn (if any)
        if self.current_rect is not None:
            painter = QPainter(pixmap)
            # Use yellow for inclusion boxes, cyan for exclusion boxes
            if self.drawing_anti:
                pen_current = QPen(Qt.cyan, 2)
            else:
                pen_current = QPen(Qt.yellow, 2)
            painter.setPen(pen_current)
            # Transform current box to view coordinates
            transformed_box = self._transform_box_to_view(self.current_rect)
            if transformed_box is not None:
                if (
                    hasattr(self.current_rect, "is_circle")
                    and self.current_rect.is_circle
                ):
                    # For circles, draw using center and radius from diameter
                    center_x = (
                        transformed_box.left() + transformed_box.right()
                    ) / 2
                    center_y = (
                        transformed_box.top() + transformed_box.bottom()
                    ) / 2
                    dx = transformed_box.right() - transformed_box.left()
                    dy = transformed_box.bottom() - transformed_box.top()
                    radius = np.sqrt(dx**2 + dy**2) / 2
                    painter.drawEllipse(
                        QPointF(center_x, center_y), radius, radius
                    )
                else:
                    painter.drawRect(transformed_box)
            painter.end()

        # Store the original pixmap before scaling for widget display
        self.ft_label._original_pixmap = pixmap

        # Update zoom parameters in the label for coordinate conversion
        full_height, full_width = self.ft_display.shape
        self.ft_label.set_zoom_params(
            self.zoom_level, self.pan_offset, (full_width, full_height)
        )

        # Scale pixmap to fit widget while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.ft_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        # Set the scaled version for display (this calls setPixmap which would overwrite _original_pixmap)
        # So we use the parent's setPixmap directly
        QLabel.setPixmap(self.ft_label, scaled_pixmap)

    def _transform_box_to_view(self, box):
        """Transform a box from full image coordinates to current zoomed view coordinates"""
        if self.ft_display is None:
            return None

        # Transform coordinates
        x1 = (box.left() - self.pan_offset.x()) * self.zoom_level
        y1 = (box.top() - self.pan_offset.y()) * self.zoom_level
        x2 = (box.right() - self.pan_offset.x()) * self.zoom_level
        y2 = (box.bottom() - self.pan_offset.y()) * self.zoom_level

        # Check if box is visible in current view
        view_height, view_width = self.ft_display.shape
        view_width *= self.zoom_level
        view_height *= self.zoom_level

        # Clip to view bounds
        if x2 < 0 or x1 > view_width or y2 < 0 or y1 > view_height:
            return None  # Box is completely outside view

        # Create transformed box
        return QRect(QPoint(int(x1), int(y1)), QPoint(int(x2), int(y2)))

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel event for zooming"""
        if self.ft_display is None:
            return

        # Get mouse position in image coordinates before zoom
        mouse_pos = self.ft_label.get_image_coordinates(event.pos())
        if mouse_pos is None:
            # If mouse is outside image, zoom around center
            full_height, full_width = self.ft_display.shape
            mouse_pos = QPoint(
                int(self.pan_offset.x() + full_width / (2 * self.zoom_level)),
                int(self.pan_offset.y() + full_height / (2 * self.zoom_level)),
            )

        # Calculate zoom factor
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 0.9

        old_zoom = self.zoom_level
        self.zoom_level *= zoom_factor

        # Clamp zoom level
        self.zoom_level = max(1.0, min(20.0, self.zoom_level))

        if self.zoom_level != old_zoom:
            # Adjust pan to keep mouse position fixed
            full_height, full_width = self.ft_display.shape

            # Calculate new pan offset to keep mouse_pos at same screen location
            # The point mouse_pos should remain at the same relative position in the view
            visible_width_old = full_width / old_zoom
            visible_height_old = full_height / old_zoom
            visible_width_new = full_width / self.zoom_level
            visible_height_new = full_height / self.zoom_level

            # Relative position of mouse in old view (0 to 1)
            if visible_width_old > 0 and visible_height_old > 0:
                rel_x = (
                    mouse_pos.x() - self.pan_offset.x()
                ) / visible_width_old
                rel_y = (
                    mouse_pos.y() - self.pan_offset.y()
                ) / visible_height_old
            else:
                rel_x = 0.5
                rel_y = 0.5

            # New pan offset to maintain same relative position
            new_pan_x = mouse_pos.x() - rel_x * visible_width_new
            new_pan_y = mouse_pos.y() - rel_y * visible_height_new

            # Clamp pan offset
            max_pan_x = full_width - visible_width_new
            max_pan_y = full_height - visible_height_new
            new_pan_x = max(0, min(max_pan_x, new_pan_x))
            new_pan_y = max(0, min(max_pan_y, new_pan_y))

            self.pan_offset = QPoint(int(new_pan_x), int(new_pan_y))

            # Redraw with new zoom
            self._update_display()

    def _on_mouse_press(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton and self.ft_display is not None:
            # Convert widget coordinates to image coordinates
            img_pos = self.ft_label.get_image_coordinates(event.pos())
            if img_pos is not None:
                self.drawing = True
                self.drawing_anti = False
                self.start_point = img_pos
                self.current_rect = QRect(self.start_point, self.start_point)
                # Mark with current shape mode
                self.current_rect.is_circle = self.shape_mode == "circle"
        elif event.button() == Qt.RightButton and self.ft_display is not None:
            # Right-click: start drawing anti-box (exclusion box)
            img_pos = self.ft_label.get_image_coordinates(event.pos())
            if img_pos is not None:
                self.drawing = True
                self.drawing_anti = True
                self.start_point = img_pos
                self.current_rect = QRect(self.start_point, self.start_point)
                # Mark with current shape mode
                self.current_rect.is_circle = self.shape_mode == "circle"
        elif event.button() == Qt.MiddleButton and self.ft_display is not None:
            # Start panning with middle mouse button
            self.panning = True
            self.pan_start = event.pos()

    def _on_mouse_move(self, event):
        """Handle mouse move event"""
        if self.drawing and self.start_point is not None:
            # Convert widget coordinates to image coordinates
            img_pos = self.ft_label.get_image_coordinates(event.pos())
            if img_pos is not None:
                new_rect = QRect(self.start_point, img_pos).normalized()
                # Preserve the shape mode flag
                new_rect.is_circle = self.shape_mode == "circle"
                self.current_rect = new_rect
                # Use fast redraw - only copy base pixmap and draw yellow box
                self._update_display(fast_redraw=True)
        elif self.panning and self.pan_start is not None:
            # Handle panning
            delta = event.pos() - self.pan_start

            # Convert pixel delta to image coordinate delta
            if self.ft_display is not None:
                full_height, full_width = self.ft_display.shape

                # Scale delta by zoom level and widget scale
                widget_width = self.ft_label.width()
                widget_height = self.ft_label.height()

                # Approximate scaling factor
                scale_x = (full_width / self.zoom_level) / widget_width
                scale_y = (full_height / self.zoom_level) / widget_height

                # Update pan offset
                new_pan_x = self.pan_offset.x() - delta.x() * scale_x
                new_pan_y = self.pan_offset.y() - delta.y() * scale_y

                # Clamp pan offset
                visible_width = full_width / self.zoom_level
                visible_height = full_height / self.zoom_level
                max_pan_x = full_width - visible_width
                max_pan_y = full_height - visible_height
                new_pan_x = max(0, min(max_pan_x, new_pan_x))
                new_pan_y = max(0, min(max_pan_y, new_pan_y))

                self.pan_offset = QPoint(int(new_pan_x), int(new_pan_y))
                self.pan_start = event.pos()

                self._update_display()

    def _on_mouse_release(self, event):
        """Handle mouse release event"""
        if (
            event.button() == Qt.LeftButton or event.button() == Qt.RightButton
        ) and self.drawing:
            self.drawing = False
            # Convert widget coordinates to image coordinates
            img_pos = self.ft_label.get_image_coordinates(event.pos())
            if img_pos is not None:
                self.current_rect = QRect(
                    self.start_point, img_pos
                ).normalized()

            if self.current_rect is not None:
                # Mark the rect with shape mode
                self.current_rect.is_circle = self.shape_mode == "circle"

                # Add to appropriate list based on drawing_anti flag
                if self.drawing_anti:
                    self.anti_boxes.append(self.current_rect)
                else:
                    self.boxes.append(self.current_rect)

            self.current_rect = None
            self.drawing_anti = False
            self._update_display()

            # Auto-apply filter after drawing box
            self._apply_filter()
        elif event.button() == Qt.MiddleButton and self.panning:
            # Stop panning
            self.panning = False
            self.pan_start = None

    def _reset_boxes(self):
        """Reset all drawn boxes and show full image"""
        self.boxes = []
        self.anti_boxes = []
        self.current_rect = None
        self._update_display()

        # Show full unfiltered image
        if self.filtered_layer_name is not None:
            self._apply_filter(show_full=True)

    def _reset_view(self):
        """Reset zoom and pan to default view"""
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self._update_display()

    def _create_mask_from_boxes(self):
        """Create a binary mask from the drawn boxes and anti-boxes

        Logic:
        - If only anti-boxes: start with full mask, subtract anti-boxes
        - If only boxes: use only the boxes
        - If both: use boxes, then subtract intersection with anti-boxes
        """
        if self.ft_data is None:
            return None

        height, width = self.ft_data.shape
        mask = np.zeros((height, width), dtype=bool)

        # Case 1: Only anti-boxes - start with full mask
        if len(self.anti_boxes) > 0 and len(self.boxes) == 0:
            mask = np.ones((height, width), dtype=bool)

        # Case 2: Boxes exist - create inclusion mask
        elif len(self.boxes) > 0:
            for box in self.boxes:
                self._apply_shape_to_mask(mask, box, True)

        # Apply anti-boxes (subtract from current mask)
        for anti_box in self.anti_boxes:
            self._apply_shape_to_mask(mask, anti_box, False)

        return mask

    def _apply_shape_to_mask(self, mask, box, include):
        """Apply a shape (rectangle or circle) to the mask

        Args:
            mask: The mask array to modify
            box: QRect defining the bounding box
            include: True to set pixels to True, False to set to False
        """
        height, width = mask.shape
        x1 = int(box.left())
        y1 = int(box.top())
        x2 = int(box.right())
        y2 = int(box.bottom())

        # Clamp to image boundaries
        x1 = max(0, min(x1, width - 1))
        x2 = max(0, min(x2, width - 1))
        y1 = max(0, min(y1, height - 1))
        y2 = max(0, min(y2, height - 1))

        if hasattr(box, "is_circle") and box.is_circle:
            # Create circular region where the two points define the diameter
            # Center is midpoint between the two points
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            # Radius is half the distance between the two points
            radius = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) / 2

            # Determine bounding box for the circle
            bbox_x1 = int(max(0, center_x - radius))
            bbox_x2 = int(min(width - 1, center_x + radius))
            bbox_y1 = int(max(0, center_y - radius))
            bbox_y2 = int(min(height - 1, center_y + radius))

            # Create coordinate grids for the bounding box
            y_coords, x_coords = np.ogrid[
                bbox_y1 : bbox_y2 + 1, bbox_x1 : bbox_x2 + 1
            ]

            # Circle equation: (x-cx)^2 + (y-cy)^2 <= r^2
            circle_mask = (x_coords - center_x) ** 2 + (
                y_coords - center_y
            ) ** 2 <= radius**2

            mask[bbox_y1 : bbox_y2 + 1, bbox_x1 : bbox_x2 + 1][
                circle_mask
            ] = include
        else:
            # Rectangular region
            mask[y1 : y2 + 1, x1 : x2 + 1] = include

    def _apply_filter(self, show_full=False):
        """Apply the inverse FFT with masking"""
        if self.ft_data is None:
            return

        # Create mask from boxes or use full mask
        if show_full:
            # Show full unfiltered image
            height, width = self.ft_data.shape
            mask = np.ones((height, width), dtype=bool)
        else:
            mask = self._create_mask_from_boxes()
            if mask is None:
                return

        # Apply mask to FFT data
        masked_ft = self.ft_data.copy()
        masked_ft[~mask] = 0

        # Inverse FFT
        unshifted = np.fft.ifftshift(masked_ft)
        filtered_image = np.fft.ifft2(unshifted)
        filtered_image = np.real(filtered_image)

        # Add or update layer in viewer
        if self.filtered_layer_name is None:
            # Create new layer with same scale as parent
            self.filtered_layer_name = (
                f"{self.current_image_layer.name}_filtered"
            )
            self.viewer.add_image(
                filtered_image,
                name=self.filtered_layer_name,
                scale=self.current_image_layer.scale,
            )
            self.info_label.setText(
                "Filtered image created. Draw more boxes to update."
            )
        else:
            # Update existing layer
            if self.filtered_layer_name in self.viewer.layers:
                layer = self.viewer.layers[self.filtered_layer_name]
                layer.data = filtered_image
                # Sync scale with parent layer
                layer.scale = self.current_image_layer.scale
                # Reset contrast limits to auto-adjust for new data
                layer.reset_contrast_limits()
            else:
                # Layer was deleted, create new one
                self.viewer.add_image(
                    filtered_image,
                    name=self.filtered_layer_name,
                    scale=self.current_image_layer.scale,
                )

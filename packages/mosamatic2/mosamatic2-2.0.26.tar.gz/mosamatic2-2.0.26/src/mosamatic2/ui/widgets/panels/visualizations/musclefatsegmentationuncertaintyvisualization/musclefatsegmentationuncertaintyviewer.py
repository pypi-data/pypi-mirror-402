import pydicom
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MuscleFatSegmentationUncertaintyViewer(FigureCanvas):
    def __init__(self, parent=None, width=14, height=7, dpi=100):
        self._figure = Figure(figsize=(width, height), dpi=dpi)
        self._axes = self._figure.subplots(1, 2)
        super(MuscleFatSegmentationUncertaintyViewer, self).__init__(self._figure)
        self.setParent(parent)
        self._image = None
        self._segmentation = None
        self._muscle_mask = None
        self._lo_hu = 30
        self._hi_hu = 150
        self._toolbar = NavigationToolbar(self, parent)

    def figure(self):
        return self._figure
    
    def axes(self):
        return self._axes
    
    def navigation_toolbar(self):
        return self._toolbar
    
    # HELPERS

    def load_data(self, image_file, segmentation_file, lo_hu, hi_hu):
        self._lo_hu = lo_hu
        self._hi_hu = hi_hu
        # Load image
        p = pydicom.dcmread(image_file)
        self._image = p.pixel_array.astype(np.float32)
        self._image = self._image * float(getattr(p, "RescaleSlope", 1.0)) + float(getattr(p, "RescaleIntercept", 0.0))
        # Load segmentation mask
        self._segmentation = np.load(segmentation_file).astype(np.uint8)
        # Initialize muscle masks
        self._muscle_mask = (self._segmentation == 1)
        overlay_muscle = self.rgba_from_binary_mask(self._muscle_mask, rgba=(1.0, 0.0, 0.0), alpha=1)
        overlay_muscle_thresholded = self.rgba_from_binary_mask_thresholded(
            self._image, self._muscle_mask, label=1, hu_lo=self._lo_hu, hu_hi=self._hi_hu, alpha=1)
        # Plot the data
        self.axes()[0].imshow(self._image, cmap='gray')
        self.axes()[0].imshow(overlay_muscle)
        self.axes()[0].axis("off")
        self.axes()[0].set_title('Muscle (red)')
        self.axes()[1].imshow(self._image, cmap="gray")
        self.axes()[1].imshow(overlay_muscle_thresholded)
        self.axes()[1].axis("off")
        self.axes()[1].set_title(f"Muscle low-RA (yellow) and high-RA (red)")
        self._figure.tight_layout()
        self.draw()

    def update_lo_hu(self, value):
        self._lo_hu = value
        self.axes()[1].clear()
        self.axes()[1].imshow(self._image, cmap="gray")
        self.axes()[1].imshow(self.rgba_from_binary_mask_thresholded(
            self._image, self._muscle_mask, label=1, hu_lo=self._lo_hu, hu_hi=self._hi_hu, alpha=1))
        self.axes()[1].axis("off")
        self.axes()[1].set_title(f"Muscle low-RA (yellow) and high-RA (red)")
        self.draw_idle()

    def update_hi_hu(self, value):
        self._hi_hu = value
        self.axes()[1].clear()
        self.axes()[1].imshow(self._image, cmap="gray")
        self.axes()[1].imshow(self.rgba_from_binary_mask_thresholded(
            self._image, self._muscle_mask, label=1, hu_lo=self._lo_hu, hu_hi=self._hi_hu, alpha=1))
        self.axes()[1].axis("off")
        self.axes()[1].set_title(f"Muscle low-RA (yellow) and high-RA (red)")
        self.draw_idle()

    def rgba_from_binary_mask(self, mask, rgba, alpha):
        out = np.zeros((*mask.shape, 4), dtype=np.float32)
        out[mask] = (rgba[0], rgba[1], rgba[2], alpha)
        return out

    def rgba_from_binary_mask_thresholded(self, image, mask, label, hu_lo, hu_hi, alpha):
        mask = (mask == label)
        red = mask & (image >= hu_lo) & (image <= hu_hi)
        yellow = mask & (image < hu_lo)
        overlay = np.zeros((*image.shape, 4), dtype=np.float32)
        overlay[red] = (1.0, 0.0, 0.0, alpha)
        overlay[yellow] = (1.0, 1.0, 0.0, alpha)
        return overlay

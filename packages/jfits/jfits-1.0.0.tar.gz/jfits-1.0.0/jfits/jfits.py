"""
jfits: Interactive FITS viewer and utilities
=============================================

A lightweight, interactive FITS file viewer built on matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.cm as cm
from matplotlib.widgets import Slider, Button, RadioButtons
from astropy.io import fits as pyfits
from astropy.wcs import WCS
import warnings

warnings.simplefilter("error", FutureWarning)
write = pyfits.writeto


def get_fits_array(filename, quiet=True, fix=False):
    """
    Read a FITS file and return header(s) and data.
    
    Parameters
    ----------
    filename : str
        Path to FITS file
    quiet : bool, optional
        If True, suppress astropy info messages (default: True)
    fix : bool, optional
        If True, attempt to fix non-standard FITS files (default: False)
        
    Returns
    -------
    header : astropy.io.fits.Header or list
        FITS header, or list of headers for multi-extension FITS
    data : ndarray or list
        Image data, or list of arrays for multi-extension FITS
        
    Examples
    --------
    >>> header, data = get_fits_array('image.fits')
    >>> print(header['OBJECT'])
    >>> plt.imshow(data)
    
    For multi-extension FITS:
    >>> headers, data_list = get_fits_array('multi.fits')
    >>> data = data_list[0]  # First extension
    """
    hdulist = pyfits.open(filename)
    if fix:
        hdulist.verify('silentfix')
    if not quiet:
        print(hdulist.info())
    if len(hdulist) > 1:
        return [hdu.header for hdu in hdulist], [hdu.data for hdu in hdulist]
    else:
        return hdulist[0].header, hdulist[0].data


def read_wcs(fits_header):
    """
    Create a WCS object from a FITS header.
    
    Parameters
    ----------
    fits_header : astropy.io.fits.Header
        FITS header containing WCS information
        
    Returns
    -------
    astropy.wcs.WCS or None
        WCS object if valid WCS found, None otherwise
        
    Examples
    --------
    >>> header, data = get_fits_array('image.fits')
    >>> wcs = read_wcs(header)
    >>> if wcs is not None:
    ...     sky = wcs.pixel_to_world(100, 200)
    ...     print(f"RA: {sky.ra.degree}, Dec: {sky.dec.degree}")
    """
    try:
        wcs = WCS(fits_header)
        # Check if WCS has celestial coordinates
        if wcs.has_celestial:
            return wcs
        else:
            return None
    except Exception as e:
        if not isinstance(e, Warning):  # Don't print warnings
            print(f"Could not parse WCS: {e}")
        return None


def safer_log(arr):
    """
    Compute logarithm of array, handling zeros and negative values safely.
    
    Parameters
    ----------
    arr : ndarray
        Input array
        
    Returns
    -------
    ndarray
        Logarithm of array, with zeros/negatives replaced by minimum positive value
        
    Examples
    --------
    >>> data = np.array([0, 1, 10, 100, -5])
    >>> log_data = safer_log(data)
    """
    positive = arr[arr > 0]
    if len(positive) > 0:
        min_pos = np.min(arr[arr > 0])
        min_replace = np.log(min_pos)
    else:
        min_replace = 0
    return np.where(arr > 0, np.log(arr), min_replace)


def make_format_coord_func(arr, scale=(1., 1.), xoffset=0, yoffset=0):
    """
    Create a coordinate formatter function for matplotlib axes.
    
    Displays pixel coordinates and values when hovering over an image.
    
    Parameters
    ----------
    arr : ndarray
        2D array being displayed
    scale : tuple of float, optional
        (y_scale, x_scale) for coordinate transformation
    xoffset : float, optional
        X offset for coordinate transformation
    yoffset : float, optional
        Y offset for coordinate transformation
        
    Returns
    -------
    function
        Formatter function for ax.format_coord
        
    Notes
    -----
    Scale is important when using extent keyword in imshow, since x and y 
    are given in data coordinates, not array coordinates.
    
    Examples
    --------
    >>> fig, ax = plt.subplots()
    >>> ax.imshow(data)
    >>> ax.format_coord = make_format_coord_func(data)
    """
    def f(x, y):
        xout = np.rint(x)
        yout = np.rint(y)
        y_idx = int(max(min(np.rint(scale[0] * y + yoffset), arr.shape[0] - 1), 0))
        x_idx = int(max(min(np.rint(scale[1] * x + xoffset), arr.shape[1] - 1), 0))
        zout = arr[y_idx, x_idx]
        
        if np.isnan(zout):
            return "x=%i, y=%i, z=NAN" % (xout, yout)
        else:
            return "x=%i, y=%i, z=%05.4e" % (xout, yout, zout)
    return f


def make_wcs_format_coord_func(arr, wcs, scale=(1., 1.), xoffset=0, yoffset=0):
    """
    Create a WCS-aware coordinate formatter function for matplotlib axes.
    
    Displays pixel coordinates, sky coordinates (RA/Dec), and values when 
    hovering over an image.
    
    Parameters
    ----------
    arr : ndarray
        2D array being displayed
    wcs : astropy.wcs.WCS
        WCS object from read_wcs()
    scale : tuple of float, optional
        (y_scale, x_scale) for coordinate transformation
    xoffset : float, optional
        X offset for coordinate transformation
    yoffset : float, optional
        Y offset for coordinate transformation
        
    Returns
    -------
    function
        Formatter function for ax.format_coord that includes RA/Dec
        
    Examples
    --------
    >>> header, data = get_fits_array('image.fits')
    >>> wcs = read_wcs(header)
    >>> fig, ax = plt.subplots()
    >>> ax.imshow(data)
    >>> ax.format_coord = make_wcs_format_coord_func(data, wcs)
    """
    def f(x, y):
        xout = np.rint(x)
        yout = np.rint(y)
        y_idx = int(max(min(np.rint(scale[0] * y + yoffset), arr.shape[0] - 1), 0))
        x_idx = int(max(min(np.rint(scale[1] * x + xoffset), arr.shape[1] - 1), 0))
        zout = arr[y_idx, x_idx]
        
        # Calculate RA/Dec using astropy.wcs
        try:
            sky = wcs.pixel_to_world(xout, yout)
            ra = sky.ra.degree
            dec = sky.dec.degree
            
            if np.isnan(zout):
                return "x=%i, y=%i | RA=%.6f deg, Dec=%.6f deg | z=NAN" % (xout, yout, ra, dec)
            else:
                return "x=%i, y=%i | RA=%.6f deg, Dec=%.6f deg | z=%05.4e" % (xout, yout, ra, dec, zout)
        except Exception:
            # Fall back to pixel coordinates only if WCS fails
            if np.isnan(zout):
                return "x=%i, y=%i | z=NAN" % (xout, yout)
            else:
                return "x=%i, y=%i | z=%05.4e" % (xout, yout, zout)
    
    return f


def Display(arr, figure=None, figsize=(8, 8), subplot=111, log=False, 
             show=True, wcs=None, **imshowargs):
    """
    Display a 2D array with matplotlib.
    
    Parameters
    ----------
    arr : ndarray
        2D array to display
    figure : matplotlib.figure.Figure, optional
        Existing figure to use. If None, creates new figure
    figsize : tuple, optional
        Figure size in inches (default: (8, 8))
    subplot : int, optional
        Subplot specification (default: 111)
    log : bool, optional
        If True, display in log scale (default: False)
    show : bool, optional
        If True, call plt.show() immediately (default: True)
    wcs : astropy.wcs.WCS, optional
        WCS object from read_wcs() for coordinate display
    **imshowargs
        Additional arguments passed to imshow (vmin, vmax, cmap, etc.)
        
    Returns
    -------
    matplotlib.axes.Axes
        The axes object containing the image
        
    Examples
    --------
    >>> data = np.random.randn(100, 100)
    >>> ax = Display(data)
    
    With WCS:
    >>> header, data = get_fits_array('image.fits')
    >>> wcs = read_wcs(header)
    >>> ax = Display(data, wcs=wcs)
    """
    if figure is None:
        f = plt.figure(figsize=figsize)
    else:
        f = figure
        
    a = f.add_subplot(subplot)
    
    if log:
        out_arr = safer_log(arr)
    else:
        out_arr = arr
        
    a.imshow(out_arr, origin='lower', interpolation='nearest', **imshowargs)
    
    # Set coordinate formatter
    if wcs is not None:
        a.format_coord = make_wcs_format_coord_func(arr, wcs)
    else:
        a.format_coord = make_format_coord_func(arr)
    
    if show:
        plt.show()
    return a


def _gaussian_2d_circular(xy, amplitude, x0, y0, sigma, offset):
    """
    Circular 2D Gaussian function (sigma_x = sigma_y, theta = 0).
    
    Parameters
    ----------
    xy : tuple of ndarray
        (x, y) coordinate arrays
    amplitude : float
        Peak amplitude above offset
    x0, y0 : float
        Center position
    sigma : float
        Gaussian width (same in x and y)
    offset : float
        Background offset
        
    Returns
    -------
    ndarray
        Flattened Gaussian values
    """
    x, y = xy
    g = offset + amplitude * np.exp(-((x - x0)**2 + (y - y0)**2) / (2 * sigma**2))
    return g.ravel()


def _gaussian_2d_elliptical(xy, amplitude, x0, y0, sigma_x, sigma_y, theta, offset):
    """
    Elliptical 2D Gaussian function with rotation.
    
    Parameters
    ----------
    xy : tuple of ndarray
        (x, y) coordinate arrays
    amplitude : float
        Peak amplitude above offset
    x0, y0 : float
        Center position
    sigma_x, sigma_y : float
        Gaussian widths in x and y
    theta : float
        Rotation angle in radians
    offset : float
        Background offset
        
    Returns
    -------
    ndarray
        Flattened Gaussian values
    """
    x, y = xy
    a = (np.cos(theta)**2) / (2 * sigma_x**2) + (np.sin(theta)**2) / (2 * sigma_y**2)
    b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
    c = (np.sin(theta)**2) / (2 * sigma_x**2) + (np.cos(theta)**2) / (2 * sigma_y**2)
    g = offset + amplitude * np.exp(-(a * (x - x0)**2 + 2 * b * (x - x0) * (y - y0) + c * (y - y0)**2))
    return g.ravel()


def _fit_gaussian_2d(data, circular=True):
    """
    Fit a 2D Gaussian to data using scipy.optimize.
    
    This is a simple implementation for interactive centroiding.
    Works well for reasonably clean point sources.
    
    Parameters
    ----------
    data : ndarray
        2D array to fit (usually a small stamp around a source)
    circular : bool, optional
        If True, fit circular Gaussian (sigma_x = sigma_y, theta = 0)
        If False, fit elliptical Gaussian with rotation (default: True)
        
    Returns
    -------
    params : dict or None
        Dictionary with fitted parameters, or None if fit fails
        Keys: 'offset', 'amplitude', 'x0', 'y0', 'sigma' (or 'sigma_x', 'sigma_y', 'theta')
        
    Notes
    -----
    This implementation uses scipy.optimize.curve_fit. Limitations:
    - May fail on very noisy data
    - Less robust than specialized astronomy fitting packages
    - Best for reasonably clean point sources in interactive use
    
    Examples
    --------
    >>> stamp = data[y-8:y+8, x-8:x+8]
    >>> result = _fit_gaussian_2d(stamp, circular=True)
    >>> if result is not None:
    ...     print(f"Centroid: ({result['x0']:.2f}, {result['y0']:.2f})")
    """
    from scipy.optimize import curve_fit
    
    height, width = data.shape
    y, x = np.indices(data.shape)
    
    # Estimate initial parameters from moments
    offset = np.median(data)
    data_centered = data - offset
    
    # Estimate amplitude
    amplitude = data.max() - offset
    if amplitude <= 0:
        return None
    
    # Estimate centroid using center of mass
    total = np.abs(data_centered).sum()
    if total == 0:
        return None
    x0 = (x * np.abs(data_centered)).sum() / total
    y0 = (y * np.abs(data_centered)).sum() / total
    
    # Estimate width from second moment
    sigma_x = np.sqrt(np.abs((((x - x0)**2) * data_centered).sum() / total))
    sigma_y = np.sqrt(np.abs((((y - y0)**2) * data_centered).sum() / total))
    sigma = (sigma_x + sigma_y) / 2.0
    
    # Make sure sigma is reasonable
    if sigma < 0.5:
        sigma = 1.0
    if sigma > min(width, height) / 2:
        sigma = min(width, height) / 4.0
    
    try:
        if circular:
            # Fit circular Gaussian (5 parameters)
            p0 = [amplitude, x0, y0, sigma, offset]
            
            popt, pcov = curve_fit(
                _gaussian_2d_circular, (x, y), data.ravel(), 
                p0=p0,
                maxfev=2000
            )
            
            # Unpack results
            amp_fit, x0_fit, y0_fit, sigma_fit, offset_fit = popt
            
            # Sanity checks
            if sigma_fit <= 0:
                print("Warning: Fit returned negative sigma")
                return None
            if abs(x0_fit - x0) > width or abs(y0_fit - y0) > height:
                print("Warning: Fit centroid far from initial guess")
                return None
            if amp_fit <= 0:
                print("Warning: Fit returned negative amplitude")
                return None
            
            return {
                'offset': offset_fit,
                'amplitude': amp_fit,
                'x0': x0_fit,
                'y0': y0_fit,
                'sigma': sigma_fit,
                'circular': True
            }
            
        else:
            # Fit elliptical Gaussian (7 parameters)
            p0 = [amplitude, x0, y0, sigma, sigma, 0.0, offset]
            
            popt, pcov = curve_fit(
                _gaussian_2d_elliptical, (x, y), data.ravel(), 
                p0=p0,
                maxfev=2000
            )
            
            # Unpack results
            amp_fit, x0_fit, y0_fit, sigma_x_fit, sigma_y_fit, theta_fit, offset_fit = popt
            
            # Sanity checks
            if sigma_x_fit <= 0 or sigma_y_fit <= 0:
                print("Warning: Fit returned negative sigma")
                return None
            if abs(x0_fit - x0) > width or abs(y0_fit - y0) > height:
                print("Warning: Fit centroid far from initial guess")
                return None
            if amp_fit <= 0:
                print("Warning: Fit returned negative amplitude")
                return None
            
            return {
                'offset': offset_fit,
                'amplitude': amp_fit,
                'x0': x0_fit,
                'y0': y0_fit,
                'sigma_x': sigma_x_fit,
                'sigma_y': sigma_y_fit,
                'theta': theta_fit,
                'circular': False
            }
        
    except (RuntimeError, ValueError) as e:
        print(f"Gaussian fit failed: {e}")
        return None


def _create_gaussian_model(params, shape):
    """
    Create a 2D Gaussian model image from fitted parameters.
    
    Parameters
    ----------
    params : dict
        Parameters from _fit_gaussian_2d()
    shape : tuple
        (height, width) of output image
        
    Returns
    -------
    model : ndarray
        2D Gaussian model
    """
    y, x = np.indices(shape)
    
    if params['circular']:
        model = _gaussian_2d_circular(
            (x, y),
            params['amplitude'],
            params['x0'],
            params['y0'],
            params['sigma'],
            params['offset']
        ).reshape(shape)
    else:
        model = _gaussian_2d_elliptical(
            (x, y),
            params['amplitude'],
            params['x0'],
            params['y0'],
            params['sigma_x'],
            params['sigma_y'],
            params['theta'],
            params['offset']
        ).reshape(shape)
    
    return model


class InteractiveDisplay:
    """
    Interactive display of 2D arrays with matplotlib widgets.
    
    Features:
    - Adjustable vmin/vmax with sliders
    - Multiple colormaps (radio buttons)
    - Linear/log scaling toggle
    - Adjustable mask color for NaN values
    - Interactive centroiding with 2D Gaussian fitting
    - WCS coordinate display (if WCS info provided)
    
    Parameters
    ----------
    arr : ndarray
        2D array to display
    figure : matplotlib.figure.Figure, optional
        Existing figure (not typically used)
    show : bool, optional
        Currently unused (interactive display always shows)
    wcs : astropy.wcs.WCS, optional
        WCS object from read_wcs() for coordinate display
    **imshowargs
        Additional arguments for imshow (vmin, vmax, etc.)
        
    Attributes
    ----------
    arr : ndarray
        The displayed array
    wcs : astropy.wcs.WCS or None
        WCS object for coordinate transforms
    fig : matplotlib.figure.Figure
        The figure
    ax : matplotlib.axes.Axes
        Main display axes
    cax : matplotlib.axes.Axes
        Colorbar axes
    
    Examples
    --------
    Basic usage:
    >>> data = np.random.randn(100, 100)
    >>> display = InteractiveDisplay(data)
    
    With WCS:
    >>> header, data = get_fits_array('image.fits')
    >>> wcs = read_wcs(header)
    >>> display = InteractiveDisplay(data, wcs=wcs)
    
    With initial settings:
    >>> display = InteractiveDisplay(data, vmin=0, vmax=1000)
    """
    
    def __init__(self, arr, figure=None, show=True, wcs=None, **imshowargs):
        self.arr = np.ma.array(arr, mask=np.isnan(arr))
        self.wcs = wcs
        self.fig = plt.figure(figsize=(10, 10))
        # Expand main axes - controls now narrower (0.10 instead of 0.15)
        self.ax = self.fig.add_axes([0.14, 0.25, 0.81, 0.70])
        cmap = cm.viridis
        cmap.set_bad('k')
        self.ax.imshow(self.arr, origin='lower', interpolation='nearest', 
                      cmap=cmap, **imshowargs)
        
        # Set up coordinate formatter
        data_ext = self.ax.images[0].get_extent()
        data_extents = (data_ext[1] - data_ext[0], data_ext[3] - data_ext[2])[::-1]
        arr_size = arr.shape
        scale_factors = list(map(lambda de, xy: xy / de, data_extents, arr_size))
        offsets = list(map(lambda e, s: s * e + 0.5, 
                          [data_ext[0], data_ext[2]], scale_factors))
        
        if wcs is not None:
            self.ax.format_coord = make_wcs_format_coord_func(
                self.arr, wcs, scale_factors, 
                xoffset=-offsets[1], yoffset=-offsets[0]
            )
        else:
            self.ax.format_coord = make_format_coord_func(
                self.arr, scale_factors, 
                xoffset=-offsets[1], yoffset=-offsets[0]
            )
        
        # Pre-compute log array for scaling
        self.logarr = safer_log(arr)
        self.data_dict = {'linear': self.arr, 'log': self.logarr}
        
        # Set up sliders
        self.min0, self.max0 = self.ax.images[0].get_clim()
        self.vmaxax = self.fig.add_axes([0.14, 0.08, 0.81, 0.03])
        self.vminax = self.fig.add_axes([0.14, 0.05, 0.81, 0.03])
        
        self.svmax = Slider(self.vmaxax, 'Vmax', self.arr.min(), self.arr.max(), 
                           valinit=self.max0)
        self.svmin = Slider(self.vminax, 'Vmin', self.arr.min(), self.arr.max(), 
                           valinit=self.min0)
        self.svmax.slidermin = self.svmin
        self.svmin.slidermax = self.svmax
        self.svmax.on_changed(self.update)
        self.svmin.on_changed(self.update)
        
        # Set up colormap selector (top box, no title)
        self.rax = self.fig.add_axes([0.025, 0.750, 0.10, 0.200])
        self.radio = RadioButtons(
            self.rax, 
            ('viridis', 'cividis', 'inferno', 'magma', 'plasma', 'gray', 'gray_r'), 
            active=0
        )
        self.radio.on_clicked(self.colorfunc)
        
        # Set up log/linear toggle (touches colormap bottom, no title)
        self.rax2 = self.fig.add_axes([0.025, 0.700, 0.10, 0.050])
        self.radio2 = RadioButtons(self.rax2, ('log', 'linear'), active=1)
        self.radio2.on_clicked(self.log_linear)
        
        # Set up mask color selector (2 buttons + title, evenly distributed)
        self.rax3 = self.fig.add_axes([0.025, 0.586, 0.10, 0.070])
        self.rax3.set_title('mask color', fontsize=10, pad=2)
        self.radio3 = RadioButtons(self.rax3, ('white', 'black'), active=1)
        self.radio3.on_clicked(self.change_mask_color)
        
        # Set up box size selector for centroiding (4 buttons + title, evenly distributed)
        self.rax5 = self.fig.add_axes([0.025, 0.422, 0.10, 0.120])
        self.rax5.set_title('centroid window size', fontsize=10, pad=2)
        self.radio5 = RadioButtons(self.rax5, ('5 pixels', '10 pixels', '20 pixels', '50 pixels'), active=1)
        self.radio5.on_clicked(self.update_box_size)
        
        # Set up centroiding controls (3 buttons + title, evenly distributed)
        self.rax4 = self.fig.add_axes([0.025, 0.284, 0.10, 0.095])
        self.rax4.set_title('centroid', fontsize=10, pad=2)
        self.radio4 = RadioButtons(self.rax4, ('Off', 'Circular', 'Elliptical'), active=0)
        self.radio4.on_clicked(self.centroid)
        
        # Track centroid mode and box size
        self.centroid_mode = None  # None, 'circular', or 'elliptical'
        self.box_size = 10  # Default box size
        
        # Spectrum figure for cube mode (will be set by child class)
        self.spectrum_fig = None
        self.show_spectrum = False
        
        # Set up colorbar
        self.cax = self.fig.add_axes([0.14, 0.17, 0.81, 0.03])
        formatter = matplotlib.ticker.ScalarFormatter()
        formatter.set_powerlimits((0, 0))
        self.cbar = self.fig.colorbar(
            self.ax.images[0], ax=self.ax, cax=self.cax, 
            orientation='horizontal', format=formatter
        )
    
    def update(self, val):
        """Update display limits when sliders change."""
        mx = self.svmax.val
        mn = self.svmin.val
        self.ax.images[0].set_clim(mn, mx)
        plt.draw()
    
    def colorfunc(self, label):
        """Change colormap when radio button clicked."""
        self.ax.images[0].set_cmap(label)
        plt.draw()
    
    def log_linear(self, label):
        """Toggle between log and linear scaling."""
        data = self.data_dict[label]
        self.ax.images[0].set_data(data)
        self.svmax.valmax = data.max()
        self.svmin.valmin = data.min()
        plt.draw()
    
    def change_mask_color(self, label):
        """Change color for masked/NaN pixels."""
        cmap = self.ax.images[0].get_cmap()
        # Convert full name to single letter for matplotlib
        color = 'w' if label == 'white' else 'k'
        cmap.set_bad(color)
        self.ax.images[0].set_cmap(cmap)
        plt.draw()
    
    def update_box_size(self, label):
        """Update box size for centroiding when radio button changes."""
        # Extract integer from label like "10 pixels"
        self.box_size = int(label.split()[0])
        if self.centroid_mode is not None:
            print(f'Box size updated to +/- {self.box_size} pixels')
    
    def onclicked(self, event):
        """
        Handle click events for centroiding.
        
        Fits a 2D Gaussian to a small region around the clicked point
        and displays the results.
        """
        if self.centroid_mode is None:
            return
        
        # Only process clicks inside the image axes
        if event.inaxes != self.ax:
            return
        
        # Update box size from radio button - extract integer from "10 pixels"
        self.box_size = int(self.radio5.value_selected.split()[0])
            
        inx = event.xdata
        iny = event.ydata
        
        if inx is None or iny is None:
            return
        
        int_inx = int(np.rint(inx))
        int_iny = int(np.rint(iny))
        print('=' * 60)
        print('Clicked position: (%.1f, %.1f)' % (inx, iny))
        print('Pixel position: (%d, %d)' % (int_inx, int_iny))
        print('Fitting mode: %s Gaussian' % self.centroid_mode)
        print('Box size: +/- %d pixels' % self.box_size)
        
        # Extract stamp around clicked point (with bounds checking)
        y_start = max(0, int_iny - self.box_size)
        y_end = min(self.arr.shape[0], int_iny + self.box_size)
        x_start = max(0, int_inx - self.box_size)
        x_end = min(self.arr.shape[1], int_inx + self.box_size)
        
        fitarr = self.arr[y_start:y_end, x_start:x_end].copy()
        
        # Fit Gaussian (circular or elliptical based on mode)
        circular = (self.centroid_mode == 'circular')
        print('Fitting 2D Gaussian...')
        params = _fit_gaussian_2d(fitarr, circular=circular)
        
        if params is None:
            print('*** Gaussian fit failed ***')
            print('  Try clicking on a cleaner/brighter source')
            print('=' * 60)
            return
        
        # Store parameters
        self.centroid_params = params
        
        # Create model for display
        stamp_model = _create_gaussian_model(params, fitarr.shape)
        
        # Place model in full-size image
        centroid_model = np.zeros_like(self.arr)
        centroid_model[y_start:y_end, x_start:x_end] = stamp_model
        self.centroid_model = centroid_model
        
        # Draw contours at 10%, 50%, 90% of peak
        peak = stamp_model.max()
        base = stamp_model.min()
        levels = base + np.array([0.1, 0.5, 0.9]) * (peak - base)
        self.ax.contour(centroid_model, levels, colors='r', linewidths=1.5)
        
        # Calculate centroid position in full image coordinates
        x_fit = params['x0'] + x_start
        y_fit = params['y0'] + y_start
        
        # Build title based on fit type
        if params['circular']:
            # Check if WCS is available
            if self.wcs is not None:
                try:
                    sky = self.wcs.pixel_to_world(x_fit, y_fit)
                    ra_fit = sky.ra.degree
                    dec_fit = sky.dec.degree
                    title_parts = [
                        'RA=%.6f deg' % ra_fit,
                        'Dec=%.6f deg' % dec_fit,
                        'sig=%.2f pix' % params['sigma'],
                        'amp=%.2e' % params['amplitude']
                    ]
                except Exception:
                    # Fall back to pixel coordinates if WCS fails
                    title_parts = [
                        'x=%.2f' % x_fit,
                        'y=%.2f' % y_fit,
                        'sig=%.2f pix' % params['sigma'],
                        'amp=%.2e' % params['amplitude']
                    ]
            else:
                title_parts = [
                    'x=%.2f' % x_fit,
                    'y=%.2f' % y_fit,
                    'sig=%.2f pix' % params['sigma'],
                    'amp=%.2e' % params['amplitude']
                ]
            # Print detailed results
            print('*** Fit successful! ***')
            print('  Centroid: (%.2f, %.2f) pixels' % (x_fit, y_fit))
            if self.wcs is not None:
                try:
                    sky = self.wcs.pixel_to_world(x_fit, y_fit)
                    print('  RA:  %.6f deg' % sky.ra.degree)
                    print('  Dec: %.6f deg' % sky.dec.degree)
                except Exception:
                    pass
            print('  Sigma: %.2f pixels' % params['sigma'])
            print('  FWHM: %.2f pixels' % (2.355 * params['sigma']))
            print('  Amplitude: %.2e' % params['amplitude'])
            print('  Offset: %.2e' % params['offset'])
        else:
            # Elliptical fit
            if self.wcs is not None:
                try:
                    sky = self.wcs.pixel_to_world(x_fit, y_fit)
                    ra_fit = sky.ra.degree
                    dec_fit = sky.dec.degree
                    title_parts = [
                        'RA=%.6f' % ra_fit,
                        'Dec=%.6f' % dec_fit,
                        'sig_x=%.2f' % params['sigma_x'],
                        'sig_y=%.2f' % params['sigma_y'],
                        'theta=%.1f deg' % np.degrees(params['theta']),
                        'amp=%.2e' % params['amplitude']
                    ]
                except Exception:
                    title_parts = [
                        'x=%.2f' % x_fit,
                        'y=%.2f' % y_fit,
                        'sig_x=%.2f' % params['sigma_x'],
                        'sig_y=%.2f' % params['sigma_y'],
                        'theta=%.1f deg' % np.degrees(params['theta']),
                        'amp=%.2e' % params['amplitude']
                    ]
            else:
                title_parts = [
                    'x=%.2f' % x_fit,
                    'y=%.2f' % y_fit,
                    'sig_x=%.2f' % params['sigma_x'],
                    'sig_y=%.2f' % params['sigma_y'],
                    'theta=%.1f deg' % np.degrees(params['theta']),
                    'amp=%.2e' % params['amplitude']
                ]
            # Print detailed results
            print('*** Fit successful! ***')
            print('  Centroid: (%.2f, %.2f) pixels' % (x_fit, y_fit))
            if self.wcs is not None:
                try:
                    sky = self.wcs.pixel_to_world(x_fit, y_fit)
                    print('  RA:  %.6f deg' % sky.ra.degree)
                    print('  Dec: %.6f deg' % sky.dec.degree)
                except Exception:
                    pass
            print('  Sigma X: %.2f pixels (FWHM: %.2f)' % (params['sigma_x'], 2.355 * params['sigma_x']))
            print('  Sigma Y: %.2f pixels (FWHM: %.2f)' % (params['sigma_y'], 2.355 * params['sigma_y']))
            print('  Rotation: %.1f degrees' % np.degrees(params['theta']))
            print('  Amplitude: %.2e' % params['amplitude'])
            print('  Offset: %.2e' % params['offset'])
        
        self.ax.set_title(' | '.join(title_parts))
        print('=' * 60)
        
        # Extract spectrum if in cube mode and spectrum display enabled
        if hasattr(self, 'show_spectrum') and self.show_spectrum:
            self.extract_and_plot_spectrum(params, x_fit, y_fit)
        
        plt.draw()

    
    def centroid(self, label):
        """
        Enable/disable centroiding mode.
        
        Parameters
        ----------
        label : str
            'Circular' for circular Gaussian fits
            'Elliptical' for elliptical Gaussian fits with rotation
            'Off' to disable and clear
        """
        if label == 'Circular':
            self.centroid_mode = 'circular'
            self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclicked)
            print('=' * 60)
            print('CIRCULAR GAUSSIAN CENTROIDING ENABLED')
            print('Click on stars to fit circular 2D Gaussians')
            print('(sigma_x = sigma_y, no rotation)')
            print(f'Box size: +/- {self.box_size} pixels')
            print('=' * 60)
            
        elif label == 'Elliptical':
            self.centroid_mode = 'elliptical'
            self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclicked)
            print('=' * 60)
            print('ELLIPTICAL GAUSSIAN CENTROIDING ENABLED')
            print('Click on stars to fit elliptical 2D Gaussians')
            print('(independent sigma_x, sigma_y, and rotation angle)')
            print(f'Box size: +/- {self.box_size} pixels')
            print('=' * 60)
            
        elif label == 'Off':
            self.centroid_mode = None
            # Clear contours
            while self.ax.collections:
                self.ax.collections[0].remove()
            
            # Clear title or preserve slice info in cube mode
            current_title = self.ax.get_title()
            if hasattr(self, 'cube'):
                # Cube mode - preserve slice info, remove centroid info
                if 'Slice' in current_title:
                    # Extract just the slice part
                    slice_part = 'Slice' + current_title.split('Slice', 1)[1]
                    self.ax.set_title(slice_part)
                else:
                    self.ax.set_title('')
            else:
                # 2D mode - clear entire title
                self.ax.set_title('')
            
            if hasattr(self, 'cid'):
                self.fig.canvas.mpl_disconnect(self.cid)
            print('Centroiding disabled')
            plt.draw()


class InteractiveDisplayCube(InteractiveDisplay):
    """
    Interactive display of 3D data cubes with slice selection.
    
    Designed for integral field spectrograph (IFS) data with structure (N, y, x)
    where N is typically the wavelength/spectral dimension.
    
    Features all InteractiveDisplay capabilities plus:
    - Slice slider to navigate through the cube
    - Current slice number and optional wavelength display
    - All other features (vmin/vmax, colormaps, centroiding, WCS)
    
    Parameters
    ----------
    cube : ndarray
        3D array with shape (N, y, x)
    figure : matplotlib.figure.Figure, optional
        Existing figure (not typically used)
    show : bool, optional
        Currently unused (interactive display always shows)
    wcs : astropy.wcs.WCS, optional
        WCS object from read_wcs() for spatial coordinate display
    wavelengths : array-like, optional
        Array of wavelength values corresponding to cube slices
        If provided, wavelength is displayed alongside slice number
    wavelength_unit : str, optional
        Unit string for wavelengths (e.g., 'nm', 'Angstrom', 'micron')
        Default: 'slice units'
    initial_slice : int, optional
        Initial slice to display (default: middle slice)
    **imshowargs
        Additional arguments for imshow (vmin, vmax, etc.)
        
    Attributes
    ----------
    cube : ndarray
        The full 3D data cube
    current_slice : int
        Currently displayed slice index
    wavelengths : array-like or None
        Wavelength array if provided
    
    Examples
    --------
    Basic cube display:
    >>> cube = np.random.randn(100, 256, 256)  # 100 wavelength slices
    >>> display = InteractiveDisplayCube(cube)
    
    With wavelength information:
    >>> wavelengths = np.linspace(0.9, 2.5, 100)  # 0.9 - 2.5 microns
    >>> display = InteractiveDisplayCube(
    ...     cube, 
    ...     wavelengths=wavelengths,
    ...     wavelength_unit='microns'
    ... )
    
    With WCS for spatial coordinates:
    >>> header, cube = get_fits_array('ifs_cube.fits')
    >>> wcs = read_wcs(header)
    >>> display = InteractiveDisplayCube(cube, wcs=wcs)
    """
    
    def __init__(self, cube, figure=None, show=True, wcs=None, 
                 wavelengths=None, wavelength_unit='slice units',
                 initial_slice=None, **imshowargs):
        
        if cube.ndim != 3:
            raise ValueError(f"cube must be 3D, got shape {cube.shape}")
        
        self.cube = cube
        self.wavelengths = wavelengths
        self.wavelength_unit = wavelength_unit
        
        # Determine initial slice
        if initial_slice is None:
            self.current_slice = cube.shape[0] // 2
        else:
            self.current_slice = max(0, min(initial_slice, cube.shape[0] - 1))
        
        # Initialize with first slice using parent class
        super().__init__(cube[self.current_slice], figure=figure, show=False, 
                        wcs=wcs, **imshowargs)
        
        # Add slice slider 
        self.slice_ax = self.fig.add_axes([0.14, 0.11, 0.81, 0.03])
        self.slice_slider = Slider(
            self.slice_ax, 
            'Slice', 
            0, 
            cube.shape[0] - 1, 
            valinit=self.current_slice,
            valstep=1
        )
        self.slice_slider.on_changed(self.update_slice)
        
        # Move colorbar up for cube mode (parent set it at 0.17)
        self.cax.set_position([0.14, 0.19, 0.81, 0.03])
        
        # Adjust vmin/vmax
        self.vminax.set_position([0.14, 0.05, 0.81, 0.03])
        self.vmaxax.set_position([0.14, 0.08, 0.81, 0.03])
        
        # Add show spectrum control for cube mode 
        self.rax_spectrum = self.fig.add_axes([0.025, 0.14, 0.10, 0.10])
        self.rax_spectrum.set_title('show spectrum', fontsize=10, pad=2)
        self.radio_spectrum = RadioButtons(self.rax_spectrum, ('no', 'yes'), active=0)
        self.radio_spectrum.on_clicked(self.toggle_spectrum)
        
        # Update title with slice info
        self._update_slice_title()
    
    def update_slice(self, val):
        """Update displayed slice when slider changes."""
        new_slice = int(self.slice_slider.val)
        
        if new_slice != self.current_slice:
            self.current_slice = new_slice
            
            # Update displayed data
            new_data = self.cube[self.current_slice]
            self.arr = np.ma.array(new_data, mask=np.isnan(new_data))
            
            # Update log version if needed
            self.logarr = safer_log(new_data)
            self.data_dict = {'linear': self.arr, 'log': self.logarr}
            
            # Update image
            current_scale = self.radio2.value_selected
            self.ax.images[0].set_data(self.data_dict[current_scale])
            
            # Update slider ranges for new slice
            self.svmax.valmax = self.arr.max()
            self.svmin.valmin = self.arr.min()
            
            # Update title
            self._update_slice_title()
            
            plt.draw()
    
    def _update_slice_title(self):
        """Update title to show current slice/wavelength info."""
        # Build slice info
        if self.wavelengths is not None:
            wave = self.wavelengths[self.current_slice]
            slice_info = 'Slice %d/%d | lambda = %.2f %s' % (
                self.current_slice, 
                self.cube.shape[0] - 1,
                wave,
                self.wavelength_unit
            )
        else:
            slice_info = 'Slice %d/%d' % (self.current_slice, self.cube.shape[0] - 1)
        
        # Check if there's centroid info in current title
        current_title = self.ax.get_title()
        
        # Extract centroid info if present (look for RA= or x= before first |)
        centroid_info = None
        if current_title and ('RA=' in current_title or 'x=' in current_title):
            # Find the centroid part (everything before "Slice")
            if 'Slice' in current_title:
                centroid_info = current_title.split('Slice')[0].rstrip(' |')
            else:
                # Whole title is centroid info
                centroid_info = current_title
        
        # Build final title
        if centroid_info:
            title = centroid_info + ' | ' + slice_info
        else:
            title = slice_info
        
        self.ax.set_title(title)
    
    def toggle_spectrum(self, label):
        """Toggle spectrum extraction on/off."""
        self.show_spectrum = (label == 'yes')
        if self.show_spectrum:
            print('Spectrum extraction enabled')
            print('  Click on source with centroiding active to extract spectrum')
        else:
            print('Spectrum extraction disabled')
            if self.spectrum_fig is not None:
                plt.close(self.spectrum_fig)
                self.spectrum_fig = None
    
    def extract_and_plot_spectrum(self, params, x_fit, y_fit):
        """
        Extract weighted spectrum from cube at fitted position.
        
        Parameters
        ----------
        params : dict
            Fitted Gaussian parameters
        x_fit, y_fit : float
            Fitted centroid position in full image coordinates
        """
        # Create 2D Gaussian weight map
        y, x = np.indices(self.arr.shape)
        
        if params['circular']:
            weights = np.exp(-((x - x_fit)**2 + (y - y_fit)**2) / (2 * params['sigma']**2))
        else:
            # Elliptical Gaussian
            theta = params['theta']
            x_rot = np.cos(theta) * (x - x_fit) - np.sin(theta) * (y - y_fit)
            y_rot = np.sin(theta) * (x - x_fit) + np.cos(theta) * (y - y_fit)
            weights = np.exp(-(x_rot**2 / (2*params['sigma_x']**2) + 
                              y_rot**2 / (2*params['sigma_y']**2)))
        
        # Normalize weights
        weights = weights / weights.sum()
        
        # Extract weighted spectrum
        spectrum = np.zeros(self.cube.shape[0])
        for i in range(self.cube.shape[0]):
            spectrum[i] = (self.cube[i] * weights).sum()
        
        # Create or update spectrum plot
        if self.spectrum_fig is None:
            self.spectrum_fig = plt.figure(figsize=(10, 6))
            self.spectrum_ax = self.spectrum_fig.add_subplot(111)
        else:
            self.spectrum_ax.clear()
        
        # Plot spectrum
        if self.wavelengths is not None:
            x_axis = self.wavelengths
            xlabel = f'Wavelength ({self.wavelength_unit})'
        else:
            x_axis = np.arange(self.cube.shape[0])
            xlabel = 'Slice index'
        
        self.spectrum_ax.plot(x_axis, spectrum, 'b-', linewidth=2)
        self.spectrum_ax.set_xlabel(xlabel, fontsize=12)
        self.spectrum_ax.set_ylabel('Weighted flux', fontsize=12)
        
        # Add title with position info
        if self.wcs is not None:
            try:
                sky = self.wcs.pixel_to_world(x_fit, y_fit)
                title = f'Spectrum at RA={sky.ra.degree:.6f} deg, Dec={sky.dec.degree:.6f} deg'
            except:
                title = f'Spectrum at (x={x_fit:.1f}, y={y_fit:.1f})'
        else:
            title = f'Spectrum at (x={x_fit:.1f}, y={y_fit:.1f})'
        
        self.spectrum_ax.set_title(title, fontsize=14)
        self.spectrum_ax.grid(True, alpha=0.3)
        
        # Mark current slice
        if self.wavelengths is not None:
            current_wave = self.wavelengths[self.current_slice]
            self.spectrum_ax.axvline(current_wave, color='r', linestyle='--', 
                                    alpha=0.5, label=f'Current slice ({self.current_slice})')
        else:
            self.spectrum_ax.axvline(self.current_slice, color='r', linestyle='--',
                                    alpha=0.5, label=f'Current slice ({self.current_slice})')
        
        self.spectrum_ax.legend()
        
        self.spectrum_fig.tight_layout()
        self.spectrum_fig.canvas.draw()
        self.spectrum_fig.show()
        
        print(f'Extracted spectrum at ({x_fit:.1f}, {y_fit:.1f})')



def quick_view_cube(filename, slice_axis=0, **kwargs):
    """
    Quick interactive view of a 3D FITS cube with slice navigation.
    
    Parameters
    ----------
    filename : str
        Path to FITS file containing 3D data
    slice_axis : int, optional
        Which axis to slice along (default: 0)
        For data shaped (N, y, x), use slice_axis=0
        For data shaped (y, x, N), use slice_axis=2
    **kwargs
        Additional arguments passed to InteractiveDisplayCube
        
    Returns
    -------
    InteractiveDisplayCube
        The interactive display object
        
    Examples
    --------
    >>> quick_view_cube('ifs_cube.fits')
    >>> quick_view_cube('cube.fits', wavelengths=np.linspace(4000, 7000, 100))
    
    Notes
    -----
    If the cube has WCS with a spectral axis, wavelength information
    may be extracted automatically in the future. Currently you need
    to provide wavelengths manually if desired.
    """
    result = get_fits_array(filename)
    
    # Handle multi-extension FITS (returns list)
    if isinstance(result[0], list):
        # Multi-extension FITS
        headers, data_list = result
        
        # Find the 3D data (usually in first extension)
        data = None
        header = None
        for i, d in enumerate(data_list):
            if d is not None and hasattr(d, 'ndim') and d.ndim == 3:
                data = d
                header = headers[i]
                break
        
        if data is None:
            raise ValueError("No 3D data found in FITS file")
    else:
        # Single HDU
        header, data = result
    
    # Ensure data is 3D
    if not hasattr(data, 'ndim') or data.ndim != 3:
        raise ValueError(f"File must contain 3D data, got shape {data.shape if hasattr(data, 'shape') else 'unknown'}")
    
    # Reorder axes if needed
    if slice_axis != 0:
        data = np.moveaxis(data, slice_axis, 0)
    
    # Try to read WCS (spatial only for now)
    wcs = read_wcs(header)
    
    if wcs is None:
        print("Note: No valid WCS found in header")
    
    # Try to extract wavelength information from header if not provided
    if 'wavelengths' not in kwargs and header is not None:
        try:
            # Check for wavelength axis info
            if 'CRVAL3' in header and 'CDELT3' in header and 'NAXIS3' in header:
                n_wave = header['NAXIS3']
                wave_start = header['CRVAL3']
                wave_delta = header['CDELT3']
                wavelengths = wave_start + np.arange(n_wave) * wave_delta
                kwargs['wavelengths'] = wavelengths
                
                # Try to get units
                if 'CUNIT3' in header:
                    kwargs['wavelength_unit'] = header['CUNIT3']
                elif 'CTYPE3' in header and 'WAVE' in header['CTYPE3']:
                    # Common units for wavelength
                    if wave_start > 1000:  # Likely Angstroms
                        kwargs['wavelength_unit'] = 'Angstrom'
                    elif wave_start > 1:  # Likely microns
                        kwargs['wavelength_unit'] = 'micron'
                    elif wave_start > 0.001:  # Likely nm
                        kwargs['wavelength_unit'] = 'nm'
                
                print(f"Detected wavelength axis: {wave_start:.2f} to {wave_start + (n_wave-1)*wave_delta:.2f} {kwargs.get('wavelength_unit', 'units')}")
        except Exception as e:
            pass  # No wavelength info available
    
    return InteractiveDisplayCube(data, wcs=wcs, **kwargs)


def quick_view(filename, **kwargs):
    """
    Quick interactive view of a FITS file with automatic WCS detection.
    
    Parameters
    ----------
    filename : str
        Path to FITS file
    **kwargs
        Additional arguments passed to InteractiveDisplay
        
    Returns
    -------
    InteractiveDisplay
        The interactive display object
        
    Examples
    --------
    >>> quick_view('image.fits')
    >>> quick_view('image.fits', vmin=0, vmax=1000)
    """
    header, data = get_fits_array(filename)
    wcs = read_wcs(header)
    
    if wcs is None:
        print("Note: No valid WCS found in header")
    
    return InteractiveDisplay(data, wcs=wcs, **kwargs)

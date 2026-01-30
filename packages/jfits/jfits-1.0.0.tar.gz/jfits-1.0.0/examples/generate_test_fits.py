"""
Generate test FITS files with WCS headers
==========================================

Creates synthetic FITS files centered on HR 8799 with proper WCS.

HR 8799 coordinates (J2000):
RA  = 23h 07m 28.7s = 346.869583 deg
Dec = +21d 08' 03"   = +21.134167 deg

Field of view: 10 arcsec x 10 arcsec
"""

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u


def create_wcs_header(ra_center, dec_center, pixscale, image_size):
    """
    Create a FITS header with WCS information.
    
    Parameters
    ----------
    ra_center : float
        RA of center in degrees
    dec_center : float
        Dec of center in degrees
    pixscale : float
        Pixel scale in arcsec/pixel
    image_size : tuple
        (ny, nx) size of image in pixels
        
    Returns
    -------
    header : astropy.io.fits.Header
        FITS header with WCS
    """
    # Create WCS object
    w = WCS(naxis=2)
    
    ny, nx = image_size
    
    # Reference pixel (center of image, FITS convention is 1-indexed)
    w.wcs.crpix = [nx/2.0, ny/2.0]
    
    # Reference coordinate (RA, Dec at reference pixel)
    w.wcs.crval = [ra_center, dec_center]
    
    # Pixel scale (degrees per pixel)
    # Negative for RA because RA increases to the East (left on sky images)
    pixscale_deg = pixscale / 3600.0  # arcsec to degrees
    w.wcs.cdelt = [-pixscale_deg, pixscale_deg]
    
    # Coordinate type
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    
    # Convert to header
    header = w.to_header()
    
    # Add some additional standard FITS keywords
    header['OBJECT'] = 'HR 8799'
    header['TELESCOP'] = 'Synthetic'
    header['INSTRUME'] = 'TestCam'
    header['FILTER'] = 'H-band'
    header['EXPTIME'] = 100.0
    header['BUNIT'] = 'counts'
    
    return header


def create_star_field_hr8799():
    """
    Create a synthetic star field centered on HR 8799.
    
    10 arcsec x 10 arcsec field
    0.05 arcsec/pixel (200x200 pixels)
    
    Planet positions from GRAVITY (unpublished) astrometry:
    - HR 8799 b: 1719 mas, PA 73.7 deg
    - HR 8799 c: 958 mas, PA 346.7 deg  
    - HR 8799 d: 701 mas, PA 246.6 deg
    - HR 8799 e: 407 mas, PA 339.1 deg
    """
    print("Creating HR 8799 star field...")
    
    # HR 8799 coordinates
    ra_hr8799 = 346.869583  # degrees
    dec_hr8799 = 21.134167  # degrees
    
    # Image parameters
    pixscale = 0.05  # arcsec/pixel
    npix = 200  # 200 x 200 pixels = 10" x 10"
    
    # Create image
    image = np.random.normal(100, 10, (npix, npix))
    
    # Add HR 8799 (central star)
    y, x = np.indices(image.shape)
    image += 10000 * np.exp(-((x - 100)**2 + (y - 100)**2) / (2*2.5**2))
    
    # Add HR 8799 b, c, d, e (the famous exoplanets!)
    # Positions from GRAVITY (unpublished), latest astrometry
    # 
    # Reference: GRAVITY Collaboration (unpublished)
    # Planet b: RA offset = 1649.724 +/- 3.076 mas, Dec offset = 483.411 +/- 1.779 mas
    # Planet c: RA offset = -220.472 +/- 0.529 mas, Dec offset = 932.572 +/- 0.709 mas
    # Planet d: RA offset = -643.389 +/- 2.129 mas, Dec offset = -278.662 +/- 1.672 mas
    # Planet e: RA offset = -145.156 +/- 0.583 mas, Dec offset = 380.078 +/- 0.643 mas
    #
    # RA/Dec offsets converted to arcsec (divide by 1000)
    companions = [
        # (RA_offset_arcsec, Dec_offset_arcsec, brightness_ratio, name)
        (1.649724, 0.483411, 0.01, 'b'),   # HR 8799 b (outermost)
        (-0.220472, 0.932572, 0.008, 'c'), # HR 8799 c
        (-0.643389, -0.278662, 0.007, 'd'),# HR 8799 d
        (-0.145156, 0.380078, 0.006, 'e'), # HR 8799 e (innermost)
    ]
    
    for ra_offset_arcsec, dec_offset_arcsec, brightness, name in companions:
        # Convert offsets to pixels
        # RA offset: negative because RA increases to the East (left)
        dx = -ra_offset_arcsec / pixscale  
        dy = dec_offset_arcsec / pixscale
        
        # Add companion
        x_comp = 100 + dx
        y_comp = 100 + dy
        
        flux = 10000 * brightness
        image += flux * np.exp(-((x - x_comp)**2 + (y - y_comp)**2) / (2*1.5**2))
    
    # Add a few background stars
    bg_stars = [
        (30, 40, 500, 2.0),
        (170, 60, 400, 2.2),
        (45, 165, 600, 1.8),
        (160, 180, 450, 2.0),
    ]
    
    for xs, ys, flux, sigma in bg_stars:
        image += flux * np.exp(-((x - xs)**2 + (y - ys)**2) / (2*sigma**2))
    
    # Create header with WCS
    header = create_wcs_header(ra_hr8799, dec_hr8799, pixscale, image.shape)
    
    # Create HDU and write
    hdu = fits.PrimaryHDU(data=image.astype(np.float32), header=header)
    hdu.writeto('hr8799_field.fits', overwrite=True)
    
    print("  Created: hr8799_field.fits")
    print(f"  Size: {npix}x{npix} pixels")
    print(f"  FOV: {npix*pixscale:.1f}\" x {npix*pixscale:.1f}\"")
    print(f"  Pixel scale: {pixscale:.3f}\"/pixel")
    print(f"  Center: RA={ra_hr8799:.6f} deg, Dec={dec_hr8799:.6f} deg")
    print(f"  Companions at ~0.4-1.7 arcsec (exoplanets b, c, d, e)")
    

def create_ifs_cube_hr8799():
    """
    Create a synthetic IFS cube of HR 8799.
    
    Simulates H-band spectrum showing methane absorption in planets.
    Planet positions match GRAVITY astrometry (same as star field).
    """
    print("\nCreating HR 8799 IFS cube...")
    
    # HR 8799 coordinates  
    ra_hr8799 = 346.869583
    dec_hr8799 = 21.134167
    
    # Spatial parameters
    pixscale = 0.05  # arcsec/pixel
    npix = 100
    
    # Spectral parameters
    n_wavelengths = 50
    wave_start = 1.5  # microns (H-band start)
    wave_end = 1.8    # microns (H-band end)
    wavelengths = np.linspace(wave_start, wave_end, n_wavelengths)
    
    # Create cube
    cube = np.zeros((n_wavelengths, npix, npix))
    y, x = np.indices((npix, npix))
    
    # Central star - flat spectrum (blackbody-like)
    star_spectrum = np.ones(n_wavelengths) * 10000
    for i in range(n_wavelengths):
        cube[i] += star_spectrum[i] * np.exp(-((x - 50)**2 + (y - 50)**2) / (2*2.5**2))
    
    # Companions with methane absorption at 1.65 microns
    # Positions from GRAVITY (unpublished), same as in star field
    # RA/Dec offsets in arcsec
    companions = [
        # (RA_offset_arcsec, Dec_offset_arcsec, base_flux, name)
        (1.649724, 0.483411, 100, 'b'),   # HR 8799 b
        (-0.220472, 0.932572, 80, 'c'),   # HR 8799 c
        (-0.643389, -0.278662, 70, 'd'),  # HR 8799 d
        (-0.145156, 0.380078, 60, 'e'),   # HR 8799 e
    ]
    
    for ra_offset_arcsec, dec_offset_arcsec, base_flux, name in companions:
        # Convert offsets to pixels
        # RA offset: negative because RA increases to the East (left)
        dx = -ra_offset_arcsec / pixscale
        dy = dec_offset_arcsec / pixscale
        
        x_comp = 50 + dx
        y_comp = 50 + dy
        
        # Create spectrum with methane absorption
        companion_spectrum = np.ones(n_wavelengths) * base_flux
        
        # Methane absorption feature around 1.65 microns
        ch4_center = 1.65
        ch4_width = 0.05
        absorption = np.exp(-((wavelengths - ch4_center)**2) / (2*ch4_width**2))
        companion_spectrum *= (1 - 0.6 * absorption)  # 60% absorption depth
        
        # Add to cube
        for i in range(n_wavelengths):
            cube[i] += companion_spectrum[i] * np.exp(-((x - x_comp)**2 + (y - y_comp)**2) / (2*1.5**2))
    
    # Add noise
    cube += np.random.normal(0, 5, cube.shape)
    
    # Add continuum background
    cube += 50
    
    # Create header (spatial WCS only)
    header = create_wcs_header(ra_hr8799, dec_hr8799, pixscale, (npix, npix))
    
    # Add spectral axis info (not full WCS, just for reference)
    header['NAXIS'] = 3
    header['NAXIS3'] = n_wavelengths
    header['CRPIX3'] = 1
    header['CRVAL3'] = wave_start
    header['CDELT3'] = (wave_end - wave_start) / (n_wavelengths - 1)
    header['CTYPE3'] = 'WAVE'
    header['CUNIT3'] = 'um'
    
    # Write cube
    hdu = fits.PrimaryHDU(data=cube.astype(np.float32), header=header)
    hdu.writeto('hr8799_ifs_cube.fits', overwrite=True)
    
    # Also save wavelength array separately
    wave_hdu = fits.ImageHDU(data=wavelengths.astype(np.float32), name='WAVELENGTH')
    hdulist = fits.HDUList([hdu, wave_hdu])
    hdulist.writeto('hr8799_ifs_cube.fits', overwrite=True)
    
    print("  Created: hr8799_ifs_cube.fits")
    print(f"  Size: {n_wavelengths}x{npix}x{npix}")
    print(f"  FOV: {npix*pixscale:.1f}\" x {npix*pixscale:.1f}\"")
    print(f"  Wavelength: {wave_start:.2f}-{wave_end:.2f} microns ({n_wavelengths} channels)")
    print(f"  Features: CH4 absorption at 1.65 microns in companions")


def create_rotated_galaxy():
    """
    Create a FITS file with a rotated elliptical galaxy.
    
    Good for testing elliptical Gaussian fitting and WCS.
    """
    print("\nCreating rotated galaxy field...")
    
    # Random field center
    ra_center = 180.0
    dec_center = 45.0
    
    pixscale = 0.2  # arcsec/pixel
    npix = 200
    
    # Create image
    image = np.random.normal(50, 5, (npix, npix))
    y, x = np.indices(image.shape)
    
    # Create elliptical galaxy
    theta = np.radians(30)
    x_rot = np.cos(theta) * (x - 100) - np.sin(theta) * (y - 100)
    y_rot = np.sin(theta) * (x - 100) + np.cos(theta) * (y - 100)
    
    sigma_x, sigma_y = 8.0, 20.0
    image += 2000 * np.exp(-(x_rot**2 / (2*sigma_x**2) + y_rot**2 / (2*sigma_y**2)))
    
    # Add a few stars
    stars = [(40, 40, 800), (160, 50, 600), (70, 170, 700)]
    for xs, ys, flux in stars:
        image += flux * np.exp(-((x - xs)**2 + (y - ys)**2) / (2*2.0**2))
    
    # Create header
    header = create_wcs_header(ra_center, dec_center, pixscale, image.shape)
    header['OBJECT'] = 'Elliptical Galaxy'
    
    # Write
    hdu = fits.PrimaryHDU(data=image.astype(np.float32), header=header)
    hdu.writeto('galaxy_rotated.fits', overwrite=True)
    
    print("  Created: galaxy_rotated.fits")
    print(f"  Size: {npix}x{npix} pixels")
    print(f"  Galaxy: elliptical, sigma_x={sigma_x:.1f}, sigma_y={sigma_y:.1f}, PA=30 deg")


def create_test_viewing_script():
    """Create a Python script to view the test files."""
    print("\nCreating viewing script...")
    
    script = '''"""
View the test FITS files created by generate_test_fits.py

Demonstrates jfits interactive features with WCS coordinates.
"""

import jfits
import matplotlib.pyplot as plt
import numpy as np

print("=" * 60)
print("jfits WCS Test Files")
print("=" * 60)

# Enable interactive mode
plt.ion()

# ============================================================
# 1. View HR 8799 star field
# ============================================================
print("\\n1. HR 8799 star field (10 arcsec x 10 arcsec)")
print("   - Central star + 4 companions (exoplanets b,c,d,e)")
print("   - Try centroiding on HR 8799 (center)")
print("   - Hover to see RA/Dec coordinates")
print("   - Companions are faint - adjust vmax slider to see them")

input("\\nPress Enter to view star field...")

try:
    display = jfits.quick_view('hr8799_field.fits')
    print("\\nTry these:")
    print("  - Enable 'Circular' centroiding")
    print("  - Click on HR 8799 (bright center star)")
    print("  - Adjust vmax to ~500 to see companions")
    print("  - Click on companions to measure positions")
except FileNotFoundError:
    print("Error: hr8799_field.fits not found")
    print("Run generate_test_fits.py first!")

input("\\nPress Enter to continue to IFS cube...")

# ============================================================
# 2. View IFS cube
# ============================================================
print("\\n2. HR 8799 IFS cube (H-band, 1.5-1.8 microns)")
print("   - Slice through wavelength")
print("   - Look for CH4 absorption at slice ~25 (1.65 microns)")
print("   - Companions show absorption, star doesn't")
print("   - Try centroiding on different slices")

try:
    # Load cube - handle multi-extension FITS
    result = jfits.get_fits_array('hr8799_ifs_cube.fits')
    
    # Check if multi-extension
    if isinstance(result[0], list):
        # Multi-extension FITS
        headers, data_list = result
        # Find the 3D cube (usually first data extension)
        header = None
        cube = None
        for i, d in enumerate(data_list):
            if d is not None and hasattr(d, 'ndim') and d.ndim == 3:
                header = headers[i]
                cube = d
                break
        
        if cube is None:
            print("Error: No 3D cube found in FITS file")
            exit(1)
    else:
        # Single HDU
        header, cube = result
    
    # Get wavelength info
    n_wave = header['NAXIS3']
    wave_start = header['CRVAL3']
    wave_delta = header['CDELT3']
    wavelengths = wave_start + np.arange(n_wave) * wave_delta
    wave_unit = header.get('CUNIT3', 'micron')
    
    # Get WCS (spatial only)
    wcs = jfits.read_wcs(header)
    
    # Display cube
    display_cube = jfits.InteractiveDisplayCube(
        cube,
        wcs=wcs,
        wavelengths=wavelengths,
        wavelength_unit=wave_unit
    )
    
    print("\\nTry these:")
    print("  - Use slice slider to navigate wavelengths")
    print("  - Watch companions fade at slice ~25 (CH4 absorption)")
    print("  - Enable 'show spectrum' and centroid on a companion")
    print("  - See the spectrum with absorption feature!")

except FileNotFoundError:
    print("Error: hr8799_ifs_cube.fits not found")
    print("Run generate_test_fits.py first!")
except Exception as e:
    print(f"Error loading cube: {e}")
    import traceback
    traceback.print_exc()

input("\\nPress Enter to continue to galaxy...")

# ============================================================
# 3. View rotated galaxy
# ============================================================
print("\\n3. Rotated elliptical galaxy")
print("   - Test elliptical Gaussian fitting")
print("   - True parameters: sigma_x=8, sigma_y=20, theta=30 deg")

try:
    display_galaxy = jfits.quick_view('galaxy_rotated.fits')
    
    print("\\nTry these:")
    print("  - Enable 'Circular' centroiding - won't fit well!")
    print("  - Switch to 'Elliptical' centroiding")
    print("  - Click on galaxy center")
    print("  - Should recover sigma_x~8, sigma_y~20, theta~30 deg")

except FileNotFoundError:
    print("Error: galaxy_rotated.fits not found")
    print("Run generate_test_fits.py first!")

print("\\n" + "=" * 60)
print("Demo complete!")
print("Close windows to exit, or explore interactively.")
print("=" * 60)

# Keep windows open
plt.show(block=True)
'''
    
    with open('view_test_fits.py', 'w') as f:
        f.write(script)
    
    print("  Created: view_test_fits.py")


def main():
    """Generate all test FITS files."""
    print("=" * 60)
    print("Generating Test FITS Files with WCS")
    print("=" * 60)
    
    create_star_field_hr8799()
    create_ifs_cube_hr8799()
    create_rotated_galaxy()
    create_test_viewing_script()
    
    print("\n" + "=" * 60)
    print("Files created successfully!")
    print("=" * 60)
    print("\nTo view:")
    print("  python view_test_fits.py")
    print("\nOr load individually:")
    print("  import jfits")
    print("  jfits.quick_view('hr8799_field.fits')")
    print("  jfits.quick_view_cube('hr8799_ifs_cube.fits')")
    print("  jfits.quick_view('galaxy_rotated.fits')")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()

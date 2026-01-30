import cv2
import numpy as np

def is_blurry_laplace(image, threshold=70):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var < threshold

def is_blurry_canny(image, threshold=1500):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Canny edge detection
    edges = cv2.Canny(gray, 100, 200)

    # Count the number of non-zero pixels (edges)
    edge_count = np.sum(edges > 0)

    # If the number of edges is below the threshold, consider the image blurry
    return edge_count < threshold

def fft_blur_check(image, threshold=150):
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Perform FFT on the image
    fft_image = np.fft.fft2(gray)
    fft_shifted = np.fft.fftshift(fft_image)
    magnitude_spectrum = 20 * np.log(np.abs(fft_shifted))

    # Calculate the blur metric from FFT
    blur_metric = np.mean(magnitude_spectrum)
    return blur_metric < threshold

def has_bright_reflections(image, threshold=240, min_area_percentage=1.0):
    """Check if image has bright reflections or glare"""
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Threshold to find very bright areas
    _, bright_areas = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # Calculate percentage of bright areas
    bright_percentage = (np.sum(bright_areas == 255) / (gray.shape[0] * gray.shape[1])) * 100
    
    # print(f"Bright Percentage: {bright_percentage}")
    return bright_percentage > min_area_percentage

def is_image_blur(image, laplace_threshold=70, canny_threshold=1500, checks_threshold=150, min_area_percentage=1.0):
    # Check using multiple methods
    conditions = []
    conditions.append(is_blurry_laplace(image, laplace_threshold))
    conditions.append(is_blurry_canny(image, canny_threshold))
    conditions.append(fft_blur_check(image, checks_threshold))
    conditions.append(has_bright_reflections(image, 240, min_area_percentage))
    
    # If 2 or more methods detect blur, consider the image blurry
    return sum(conditions) >= 2 
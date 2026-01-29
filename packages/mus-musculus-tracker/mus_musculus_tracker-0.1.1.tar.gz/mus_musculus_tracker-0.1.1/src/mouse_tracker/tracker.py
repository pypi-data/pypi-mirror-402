"""
Video Cropping and Object Tracking Script
Description: Allows user to select a center point, crops the video around it, 
and uses YOLO to track objects while generating a trajectory (trail) and a CSV log.

Install dependencies using:
conda env create -f environment.yml
conda activate mouse-tracker

How to run:
$ mouse-track your_video.mp4
"""

from moviepy.video.io.VideoFileClip import VideoFileClip
import cv2
import sys
from pathlib import Path
import ultralytics
from ultralytics import YOLO
import csv
import numpy as np
from tqdm import tqdm

# Initialize Ultralytics checks
ultralytics.checks()

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = PACKAGE_DIR / "weights" / "best.pt"

def select_point(event, x, y, flags, param):
    """Mouse callback to capture the center coordinates for cropping."""
    if event == cv2.EVENT_LBUTTONDOWN:
        param['point'] = (x, y)
        param['frame_copy'] = param['frame'].copy()
        # Draw a visual marker for the selection
        cv2.circle(param['frame_copy'], (x, y), 6, (0, 0, 255), 5)
        cv2.imshow('Select Center Point', param['frame_copy'])
        print(f"Point selected: ({param['point']})")

def crop_video_borders(video_path, center_of_coordinates, h, w):
    """Crops the video around a center point and resizes to 640x640."""
    video = VideoFileClip(video_path)
    
    # Calculate crop boundaries based on the height (creating a square)
    cropped_video = video.cropped(
        x1=center_of_coordinates[0] - h // 2,
        x2=center_of_coordinates[0] + h // 2
    ).resized((640, 640))
    
    p = Path(video_path)
    output_filename = str(p.with_name(p.stem + "_cropped" + p.suffix))

    # Save using libx264 codec for universal compatibility
    cropped_video.write_videofile(output_filename, codec="libx264", audio_codec="aac")
    
    video.close()
    cropped_video.close()
    
    print(f"Video successfully cropped and saved as: {output_filename}")
    return output_filename

def yolo_track(cropped_video_filename):
    """Runs YOLO tracking, draws trajectory trails, and logs data to CSV."""
    # Load your custom model
    model = YOLO(str(DEFAULT_MODEL_PATH))

    results_generator = model.track(
        cropped_video_filename,
        conf=0.5,
        iou=0,
        max_det=1, # Optimized for tracking a single subject
        persist=True,
        save=True,
        show_labels=False,
        show_conf=False,
        tracker="botsort.yaml", 
        stream=True,
        verbose=False,
    )

    # Get video metadata
    cap = cv2.VideoCapture(cropped_video_filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print(f"Video properties: {fps:.2f} FPS | Total Frames: {total_frames}")

    # Configure VideoWriter for the annotated output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_path = f"{cropped_video_filename[:-4]}_tracked.mp4"
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
    
    # Prepare CSV log file
    log_filename = f"{cropped_video_filename[:-4]}_log.csv"
    with open(log_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Frame", "Track_ID", "Class", "Time (s)", "Confidence", "pos_x", "pos_y", "center_x", "center_y"])

    frame_index = 0
    trails = [] # Stores coordinate history for trajectory drawing

    print("\nProcessing tracking and generating logs...")

    for result in tqdm(results_generator, total=total_frames, unit="frames"):
        frame = result.orig_img

        if result.boxes:
            boxes = result.boxes.cpu().numpy()
            track_ids = boxes.id if boxes.id is not None else [-1] * len(boxes)

            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box.xywh[0]
                confidence = box.conf[0]
                cls_id = int(box.cls[0])
                class_name = result.names[cls_id]
                time_stamp = frame_index / fps

                current_point = (int(x), int(y))

                # Update trajectory if coordinates are within frame
                if 0 <= int(y) < height and 0 <= int(x) < width:
                    trails.append(current_point)

                # Draw trajectory trail
                if len(trails) > 1:
                    points_array = np.array(trails, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(frame, [points_array], isClosed=False, color=(0, 255, 255), thickness=2)

                # Draw current detection point
                cv2.circle(frame, current_point, radius=3, color=(0, 0, 255), thickness=-1)

                # Write data to CSV
                with open(log_filename, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        frame_index, int(track_id), class_name, 
                        f"{time_stamp:.3f}", f"{confidence:.4f}", 
                        f"{x:.1f}", f"{y:.1f}", "320", "320"
                    ])
        else:
            # Continue drawing trail even if detection is lost in current frame
            if len(trails) > 1:
                points_array = np.array(trails, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [points_array], isClosed=False, color=(0, 255, 255), thickness=2)

        out.write(frame)
        frame_index += 1

    out.release()
    print(f"Tracking complete. Log saved to: {log_filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: mouse-track <mp4_video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video file.")
        sys.exit(1)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Error: Could not read the first frame.")
        sys.exit(1)
    
    h, w = frame.shape[:2]
    params = {'point': None, 'frame': frame, 'frame_copy': frame.copy()}

    # GUI for point selection
    cv2.namedWindow('Select Center Point', cv2.WINDOW_GUI_NORMAL)
    cv2.resizeWindow('Select Center Point', 1280, 1280)
    cv2.setMouseCallback('Select Center Point', select_point, params)
    cv2.imshow('Select Center Point', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    center_of_coordinates = params['point']
    if center_of_coordinates is None:
        print("No point selected. Exiting.")
        sys.exit(0)

    # Workflow prompts
    response = input("\nProceed with cropping? (y/n): ").lower()
    if response == 'y':
        cropped_video_filename = crop_video_borders(video_path, center_of_coordinates, h, w)
    else:
        sys.exit(0)

    response = input("\nProceed with tracking? (y/n): ").lower()
    if response == 'y':
        yolo_track(cropped_video_filename)
    else:
        sys.exit(0)

    print("Script finished successfully!")

if __name__ == "__main__":
    main()
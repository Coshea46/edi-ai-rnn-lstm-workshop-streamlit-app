"""Video, pose and quiz helpers. No model service or cloud storage required."""
from pathlib import Path
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw

DATA_DIR = Path(__file__).resolve().parent / 'data'
# COCO-17 connections, with player roles A and B, not guaranteed identities.
BONES = [(0,1),(0,2),(1,3),(2,4),(5,6),(5,7),(7,9),(6,8),(8,10),
         (5,11),(6,12),(11,12),(11,13),(13,15),(12,14),(14,16)]
PLAYER_COLOURS = [(8,127,140), (207,91,49)]


def load_catalogue(data_dir=DATA_DIR):
    data_dir = Path(data_dir)
    clips = json.loads((data_dir / 'catalogue.json').read_text())
    ids = [clip['id'] for clip in clips]
    if len(set(ids)) != len(ids):
        raise ValueError('Clip IDs must be unique.')
    with np.load(data_dir / 'poses.npz', allow_pickle=False) as archive:
        for clip in clips:
            if clip['role'] not in ('guided', 'practice', 'quiz') or clip['label'] not in (0,1):
                raise ValueError('Invalid clip role or label.')
            if not (data_dir / clip['video']).is_file():
                raise FileNotFoundError(clip['video'])
            if archive[clip['id']].shape != (210,68) or not np.isfinite(archive[clip['id']]).all():
                raise ValueError('Expected finite [210,68] pose arrays.')
    return clips


def load_poses(data_dir=DATA_DIR):
    with np.load(Path(data_dir) / 'poses.npz', allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def video_info(path):
    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            raise ValueError('Could not open the example video.')
        return {
            'frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': float(cap.get(cv2.CAP_PROP_FPS)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
    finally:
        cap.release()


def read_frame(path, index):
    cap = cv2.VideoCapture(str(path))
    try:
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if not cap.isOpened() or not 0 <= index < count:
            raise ValueError('Frame index is outside the video.')
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        success, bgr = cap.read()
        if not success:
            raise ValueError('Could not decode the selected frame.')
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    finally:
        cap.release()


def draw_pose(frame, coordinates, skeleton_only=False, selected_joint=None):
    """Plot the actual exported pose for this frame; omit unresolved joints."""
    height, width = frame.shape[:2]
    image = Image.new('RGB', (width,height), '#F7FAF9') if skeleton_only else Image.fromarray(frame)
    draw = ImageDraw.Draw(image)
    players = np.asarray(coordinates).reshape(2,17,2)
    for player, colour in zip(players, PLAYER_COLOURS):
        valid = np.isfinite(player).all(axis=1) & (player > 0).all(axis=1) & (player <= 1).all(axis=1)
        points = [(int(x*width), int(y*height)) for x,y in player]
        for a,b in BONES:
            if valid[a] and valid[b]:
                draw.line((points[a],points[b]),fill=colour,width=3)
        for joint,(x,y) in enumerate(points):
            if valid[joint]:
                r = 6 if joint == selected_joint else 3
                draw.ellipse((x-r,y-r,x+r,y+r),fill=colour,outline='white',width=1)
    return image


def pixel_patch(frame, x, y, radius=5, scale=22):
    """Magnify a small RGB pixel grid and outline the selected pixel."""
    height,width=frame.shape[:2]
    x,y=int(x),int(y)
    if not (0<=x<width and 0<=y<height):
        raise ValueError('Pixel coordinates are outside the image.')
    left,right=max(0,x-radius),min(width,x+radius+1)
    top,bottom=max(0,y-radius),min(height,y+radius+1)
    patch=Image.fromarray(frame[top:bottom,left:right]).resize(((right-left)*scale,(bottom-top)*scale),Image.Resampling.NEAREST)
    draw=ImageDraw.Draw(patch)
    for xx in range(0,patch.width,scale):draw.line((xx,0,xx,patch.height),fill='#8D9C9D')
    for yy in range(0,patch.height,scale):draw.line((0,yy,patch.width,yy),fill='#8D9C9D')
    xx,yy=(x-left)*scale,(y-top)*scale
    draw.rectangle((xx,yy,xx+scale-1,yy+scale-1),outline='#EE3158',width=3)
    return patch


def rgb_and_bits(frame,x,y):
    rgb=tuple(int(v) for v in frame[int(y),int(x)])
    return rgb,tuple(format(value,'08b') for value in rgb)


def score_answers(clips, answers):
    """Score only after one explicit answer exists for every final clip."""
    if set(answers) != {clip['id'] for clip in clips}:
        raise ValueError('Answer every final clip before revealing the results.')
    if any(answer not in (0,1) for answer in answers.values()):
        raise ValueError('Answers must be attempt or no attempt.')
    rows=[{'clip':clip['title'],'answer':answers[clip['id']], 'label':clip['label'],
           'correct':answers[clip['id']]==clip['label']} for clip in clips]
    return sum(row['correct'] for row in rows),rows

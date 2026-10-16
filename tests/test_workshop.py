import unittest
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import DATA_DIR,load_catalogue,load_poses,read_frame,video_info,draw_pose,pixel_patch,rgb_and_bits,score_answers

class WorkshopChecks(unittest.TestCase):
    def test_assets_align_and_first_and_last_frames_decode(self):
        poses=load_poses()
        for clip in load_catalogue():
            info=video_info(DATA_DIR/clip['video'])
            self.assertEqual(info['frames'],210)
            self.assertAlmostEqual(info['fps'],30)
            for i in [0,209]:
                frame=read_frame(DATA_DIR/clip['video'],i)
                self.assertEqual(frame.shape,(info['height'],info['width'],3))
                image=draw_pose(frame,poses[clip['id']][i],True)
                self.assertEqual(image.size,(info['width'],info['height']))

    def test_pixel_values_and_binary_are_actual_rgb(self):
        pixels=np.array([[[0,127,255],[10,20,30]],[[255,0,0],[0,0,0]]],dtype=np.uint8)
        rgb,bits=rgb_and_bits(pixels,0,0)
        self.assertEqual(rgb,(0,127,255))
        self.assertEqual(bits,('00000000','01111111','11111111'))
        # A corner selection must also yield a valid magnified image.
        self.assertEqual(pixel_patch(pixels,0,0).size,(44,44))

    def test_final_quiz_requires_all_answers_and_scores_correctly(self):
        clips=[c for c in load_catalogue() if c['role']=='quiz']
        with self.assertRaises(ValueError):score_answers(clips,{})
        correct={c['id']:c['label'] for c in clips}
        self.assertEqual(score_answers(clips,correct)[0],len(clips))
        wrong={key:1-value for key,value in correct.items()}
        self.assertEqual(score_answers(clips,wrong)[0],0)
        self.assertTrue(set(c['id'] for c in clips).isdisjoint(c['id'] for c in load_catalogue() if c['role']=='practice'))

    def test_unresolved_pose_is_not_drawn_as_an_athlete_at_origin(self):
        blank=np.zeros((30,40,3),dtype=np.uint8)
        image=np.asarray(draw_pose(blank,np.zeros(68),True))
        self.assertTrue(np.all(image==np.array([247,250,249])))
        with self.assertRaises(ValueError):read_frame(DATA_DIR/load_catalogue()[0]['video'],210)

if __name__=='__main__':unittest.main()

from pathlib import Path
from streamlit.testing.v1 import AppTest
app=Path(__file__).resolve().parents[1] / 'app.py'
at=AppTest.from_file(str(app),default_timeout=30).run()
def check(label):
    assert not at.exception,[e.message for e in at.exception]
    print('PASS',label,flush=True)
def nav(page):
    next(s for s in at.selectbox if s.label=='Workshop steps').set_value(page).run();check(page)

def click_button(key):
    next(b for b in at.button if b.key==key).click().run();check(key)

check('Start')
assert next(b for b in at.button if b.key=='top_back').disabled
click_button('top_next')
assert at.session_state['workshop_page']=='1 · Video is pictures'
assert any('What to do' in m.value for m in at.markdown)
at.slider[0].set_value(210).run();check('last video frame')
next(s for s in at.selectbox if s.label=='Choose an example').set_value(1).run()
next(r for r in at.radio if r.label=='What do you see in this guided example?').set_value('An attempt').run()
next(s for s in at.slider if s.label.startswith('Mark where')).set_value((70,130)).run();check('attempt interval')
image_captions = [image.caption for element in at.get('image') for image in element.proto.imgs]
assert any('Your start: frame 70' in caption for caption in image_captions)
assert any('Your end: frame 130' in caption for caption in image_captions)
assert any('not a scored answer' in i.value for i in at.info)
next(r for r in at.radio if r.label=='What do you see in this guided example?').set_value('No attempt').run()
assert not any(s.label.startswith('Mark where') for s in at.slider)
click_button('bottom_next')
assert at.session_state['workshop_page']=='2 · Pictures are numbers'
click_button('top_back')
assert at.session_state['workshop_page']=='1 · Video is pictures'
nav('2 · Pictures are numbers')
for slider in at.slider:
    if slider.label.startswith('Pixel position'):slider.set_value(0)
at.run();check('corner pixel')
nav('3 · Players become skeletons')
for mode in ['Skeleton overlay','Skeleton only','Original picture']:
    next(r for r in at.radio if r.label=='View').set_value(mode).run();check(mode)
nav('4 · Find a pattern')
next(t for t in at.text_area if t.label=='Your current rule').set_value('Look for a turn followed by a loss of balance.').run()
next(r for r in at.radio if r.label=='Your prediction').set_value('Attempt').run()
next(b for b in at.button if b.label=='Reveal this practice label').click().run();check('practice reveal')
nav('5 · Final quiz')
assert next(t for t in at.text_area if t.label=='Your final rule').value=='Look for a turn followed by a loss of balance.'
next(t for t in at.text_area if t.label=='Your final rule').set_value('My final rule.').run()
click_button('bottom_back')
assert next(t for t in at.text_area if t.label=='Your current rule').value=='Look for a turn followed by a loss of balance.'
click_button('top_next')
assert next(t for t in at.text_area if t.label=='Your final rule').value=='My final rule.'
assert not at.success
next(b for b in at.button if b.label.startswith('Submit all predictions')).click().run();check('incomplete quiz')
assert any('Answer every' in w.value for w in at.warning)
for r in at.radio:
    if r.label.startswith('Prediction for Final'):r.set_value('Attempt' if r.label.endswith('A') else 'No attempt')
next(b for b in at.button if b.label.startswith('Submit all predictions')).click().run();check('complete quiz')
assert at.session_state['quiz_submitted']
assert at.session_state['quiz_score']==2
assert not any(b.label.startswith('Submit all predictions') for b in at.button)
click_button('top_back')
click_button('bottom_next')
assert at.session_state['quiz_score']==2
assert not any(b.label.startswith('Submit all predictions') for b in at.button)
print('ALL UI CHECKS PASSED',flush=True)

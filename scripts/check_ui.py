from pathlib import Path
from streamlit.testing.v1 import AppTest
app=Path(__file__).resolve().parents[1] / 'app.py'
at=AppTest.from_file(str(app),default_timeout=30).run()
def check(label):
    assert not at.exception,[e.message for e in at.exception]
    print('PASS',label,flush=True)
def nav(page):
    at.sidebar.radio[0].set_value(page).run();check(page)
check('Start')
nav('1 · Video is pictures')
at.slider[0].set_value(210).run();check('last video frame')
nav('2 · Pictures are numbers')
for slider in at.slider:
    if slider.label.startswith('Pixel position'):slider.set_value(0)
at.run();check('corner pixel')
nav('3 · Players become skeletons')
for mode in ['Skeleton overlay','Skeleton only','Original picture']:
    next(r for r in at.radio if r.label=='View').set_value(mode).run();check(mode)
nav('4 · Find a pattern')
next(r for r in at.radio if r.label=='Your prediction').set_value('Attempt').run()
next(b for b in at.button if b.label=='Reveal this practice label').click().run();check('practice reveal')
nav('5 · Final quiz')
next(b for b in at.button if b.label.startswith('Submit all predictions')).click().run();check('incomplete quiz')
assert any('Answer every' in w.value for w in at.warning)
for r in at.radio:
    if r.label.startswith('Prediction for Final'):r.set_value('Attempt' if r.label.endswith('A') else 'No attempt')
next(b for b in at.button if b.label.startswith('Submit all predictions')).click().run();check('complete quiz')
assert at.session_state['quiz_submitted']
assert at.session_state['quiz_score']==2
assert not any(b.label.startswith('Submit all predictions') for b in at.button)
print('ALL UI CHECKS PASSED',flush=True)

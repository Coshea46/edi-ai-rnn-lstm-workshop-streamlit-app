"""Run with: streamlit run app.py"""
import streamlit as st
from PIL import Image, ImageDraw

from core import (
    DATA_DIR, load_catalogue, load_poses, read_frame,
    draw_pose, pixel_patch, rgb_and_bits, score_answers,
)

st.set_page_config(page_title='How computers see movement · Edinburgh AI',page_icon='🥋',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
/* Leave room for Streamlit's fixed header above the workshop navigation. */
.block-container {max-width:1180px;padding-top:6rem;padding-bottom:3rem;}
[data-testid="stSidebar"] {border-right:1px solid #d5e1df;}
h1,h2,h3 {letter-spacing:-.025em;}
.stCaption {line-height:1.5;}
</style>''',unsafe_allow_html=True)


@st.cache_data
def catalogue():return load_catalogue()

@st.cache_data
def poses():return load_poses()

@st.cache_data(max_entries=32,show_spinner=False)
def frame_at(clip_id,index):
    clip=next(c for c in catalogue() if c['id']==clip_id)
    return read_frame(DATA_DIR / clip['video'],index)

@st.cache_data
def video_bytes(clip_id):
    clip=next(c for c in catalogue() if c['id']==clip_id)
    return (DATA_DIR / clip['video']).read_bytes()


def play(clip):
    st.video(video_bytes(clip['id']),format='video/mp4')


def choose_guided(key):
    clips=[c for c in catalogue() if c['role']=='guided']
    chosen=st.selectbox('Choose an example',range(len(clips)),format_func=lambda i:clips[i]['title'],key=key)
    return clips[chosen]


def frame_slider(clip,key):
    # The slider inspects still frames independently of the video player's playhead.
    index=st.slider('Frame',1,clip['frames'],61,key=f'{key}_{clip["id"]}')-1
    st.caption(f'Frame {index+1} of {clip["frames"]} · {index/clip["fps"]:.2f} seconds into the clip')
    return index,frame_at(clip['id'],index)


PAGES = [
    'Start here', '1 · Video is pictures', '2 · Pictures are numbers',
    '3 · Players become skeletons', '4 · Find a pattern', '5 · Final quiz',
]


def go_to(page):
    st.session_state['workshop_page'] = page


def navigation_buttons(position):
    index = PAGES.index(st.session_state['workshop_page'])
    back, next_step = st.columns(2)
    back.button('← Back', disabled=index == 0, key=f'{position}_back',
                on_click=go_to, args=(PAGES[max(0, index-1)],), width='stretch')
    if index < len(PAGES)-1:
        label = 'Start activity 1 →' if index == 0 else f'Next: {PAGES[index+1]} →'
        next_step.button(label, type='primary', key=f'{position}_next',
                         on_click=go_to, args=(PAGES[index+1],), width='stretch')
    else:
        next_step.caption('Last activity · Submit both predictions to see your results.'
                          if not st.session_state.get('quiz_submitted') else 'You have reached the end of the workshop.')


def task_intro(steps, why):
    with st.container(border=True):
        st.markdown('**What to do**')
        st.markdown('\n'.join(f'{i}. {step}' for i, step in enumerate(steps, 1)))
        st.markdown(f'**Why we are doing this:** {why}')


def attempt_guide():
    with st.container(border=True):
        st.markdown('**What counts as an attempt, and when does it start?**')
        st.write('Look for one person trying to make the other fall. Count an attempt even if the other person keeps their balance and stays standing.')
        st.write('Start at the first movement into the position used to try to make the other person fall. '
                 'For example, they might begin turning their body across the other person, move their hips underneath them, '
                 'or bring a leg towards the other person’s legs to trip them. Start with that movement into position; do not wait for someone to leave the ground or fall.')
        st.write('Walking around together, holding each other’s clothing or pulling on it does not by itself count. '
                 'Look at the pictures before and after to decide whether a movement is part of trying to make the other person fall.')
        st.write('For the end, choose when that try has finished: they return to standing movement, or the falling movement has settled on the mat.')


def remember_rule(widget_key, saved_key):
    st.session_state[saved_key] = st.session_state[widget_key]


with st.sidebar:
    st.markdown('### EDINBURGH AI')
    st.title('How computers\nsee movement')
    st.caption('No code. No maths background.\nUse the examples and your own observations.')
    st.link_button('See Judo Clipper ↗','https://www.judoclipper.com/')

st.selectbox('Workshop steps', PAGES, key='workshop_page',
             help='Work through the steps in order using Back and Next. You can also choose a step here.')
page = st.session_state['workshop_page']
step = PAGES.index(page)
st.progress(step / (len(PAGES)-1), text='Introduction · then five activities' if step == 0 else f'Activity {step} of 5')
navigation_buttons('top')
st.divider()

if page=='Start here':
    st.caption('SPORTS VISION / A BEGINNER WORKSHOP')
    st.title('How does a computer spot a throw?')
    st.write('A coach wants to review the important moments in a judo match. Our job is to explore how a computer could help find them.')
    task_intro([
        'Read what we mean by a throw attempt below, then watch the example.',
        'Choose “Start activity 1” to begin. Use Next and Back above or below each activity.',
    ], 'You will use the same question throughout: does a seven-second clip contain at least one attempt to make the other person fall?')
    a,b=st.columns([1,1.15],gap='large')
    with a:
        st.subheader('First, what counts as a throw attempt?')
        st.write('In this sport, called judo, two people hold each other’s clothing and try to make the other person fall onto their back.')
        st.write('An attempt counts even if the other person keeps their balance and stays standing.')
        st.markdown('**The question:** does this seven-second clip contain at least one throw attempt?')
    with b:
        play(next(c for c in catalogue() if c['id']=='attempt_id960'))
        st.caption('An example containing a throw attempt. Look for the first move into position, then the effort to make the other person fall.')
    attempt_guide()
    st.subheader('The idea we will build')
    st.write('A video is a sequence of pictures. Pictures can be represented with numbers. Joint positions give us a smaller set of numbers that describes the athletes. A sequence model learns patterns in how those numbers change over time.')

elif page=='1 · Video is pictures':
    st.title('A video is a sequence of still pictures')
    task_intro([
        'Watch an example all the way through. You can choose either example below.',
        'Move the Frame slider to inspect individual pictures and compare the pictures shown in time order.',
        'Below the pictures, say whether you see an attempt. If you do, use the two handles to mark where it starts and ends.',
    ], 'An action unfolds across several pictures. Finding its beginning and end helps you see why their order matters.')
    st.write('Showing the pictures quickly makes us perceive movement. Each picture is called a frame. This clip has 30 frames every second: seven seconds gives us 210 frames.')
    attempt_guide()
    clip=choose_guided('flipbook_clip')
    left,right=st.columns(2,gap='large')
    with left:
        st.subheader('Watch the video')
        play(clip)
    with right:
        st.subheader('Inspect one picture')
        index,frame=frame_slider(clip,'flipbook')
        st.image(frame,width="stretch")
        st.caption('The frame slider is a separate inspection tool. It does not move the video player.')
    st.subheader('A few pictures in time order')
    chosen=sorted(set(max(0,min(209,index+offset)) for offset in [-30,0,30]))
    for col,i in zip(st.columns(len(chosen)),chosen):
        col.image(frame_at(clip['id'],i),caption=f'Frame {i+1}',width="stretch")
    st.subheader('Mark the part where the attempt happens')
    observation = st.radio('What do you see in this guided example?',
                           ['Choose an answer', 'An attempt', 'No attempt'], key=f'interval_answer_{clip["id"]}')
    if observation == 'An attempt':
        start, end = st.slider('Mark where the attempt starts and ends (frame numbers)',
                               1, clip['frames'], (1, clip['frames']), key=f'attempt_interval_{clip["id"]}')
        st.caption('Move the left handle to the first movement into position. Move the right handle to where that try finishes. '
                   'Use the Frame slider above to look closely; these handles do not move the video player.')
        for col, label, number in zip(st.columns(2), ['Your start', 'Your end'], [start, end]):
            col.image(frame_at(clip['id'], number-1),
                      caption=f'{label}: frame {number} · {(number-1)/clip["fps"]:.2f} seconds', width='stretch')
        st.info('This range is your observation, not a scored answer. The supplied labels tell us whether the whole clip contains an attempt; they do not give exact start and end frames.')
    elif observation == 'No attempt':
        st.info('If you see no attempt, there is no start or end to mark. Movement alone does not mean someone is trying to make the other person fall.')
    st.markdown('**Discuss:** what does the sequence tell you that one frozen picture cannot? What would change if we shuffled these pictures?')

elif page=='2 · Pictures are numbers':
    st.title('A picture is a grid of coloured squares')
    task_intro([
        'Choose a picture with the Frame slider.',
        'Move the two Pixel position sliders until the pink marker is on someone’s clothing. Read the red, green and blue numbers, then try a spot on the mat.',
        'Keep the pixel position the same and change the frame. See how the colour numbers change as people move past that spot.',
    ], 'You are seeing the colour numbers a computer can work with, and the patterns of ones and zeros used to store them.')
    st.write('These tiny squares are pixels. A bitmap represents a picture as a grid of pixels, with numbers describing their colours. In the RGB representation below, each pixel has red, green and blue values from 0 to 255.')
    clip=choose_guided('pixel_clip')
    index,frame=frame_slider(clip,'pixels')
    height,width=frame.shape[:2]
    x=st.slider('Pixel position across the picture (x)',0,width-1,width//2,key=f'px_{clip["id"]}')
    y=st.slider('Pixel position down the picture (y)',0,height-1,height//2,key=f'py_{clip["id"]}')
    annotated=Image.fromarray(frame)
    draw=ImageDraw.Draw(annotated)
    draw.rectangle((max(0,x-5),max(0,y-5),min(width-1,x+5),min(height-1,y+5)),outline='#EE3158',width=2)
    a,b=st.columns([1.6,1],gap='large')
    with a:
        st.image(annotated,caption='The pink marker locates your selected pixel.',width="stretch")
    with b:
        st.image(pixel_patch(frame,x,y),caption='A tiny part of the picture, enlarged. The pink square is one pixel.',width=280)
    rgb,bits=rgb_and_bits(frame,x,y)
    st.subheader('The numbers for your selected pixel')
    cols=st.columns(3)
    for col,name,value,binary in zip(cols,['Red','Green','Blue'],rgb,bits):
        col.metric(name,value)
        col.caption(f'As eight binary digits: {binary}')
    st.write('The computer stores these numbers using ones and zeros. You do not need to memorise binary: the important point is that a picture can be represented numerically.')
    st.markdown('**Think about it:** when the colour at your chosen spot changes, how do its three numbers change?')
    st.info('More movement does not mean more ones. Movement changes the arrangement and values of the pixels. Video files also compress information to save space; they do not simply store every frame as a separate bitmap.')

elif page=='3 · Players become skeletons':
    st.title('Which numbers would help us find a throw?')
    task_intro([
        'Choose an example and a frame. Switch from “Original picture” to “Skeleton overlay” to see the estimated body points drawn on the picture.',
        'Choose “Skeleton only” to hide the picture behind those points. Select a body point with “Highlight a joint” and read its position below.',
        'Move through a few frames. Compare what you can still see with what has disappeared. Open “Watch this skeleton sequence move” to see the points moving together.',
    ], 'Body positions give the computer fewer numbers to work with when looking for a throw, and reduce information about the crowd, signs and mat.')
    st.write('The athletes matter more to our task than the advertising boards or the crowd. A pose-estimation model locates joints such as shoulders, hips and knees. We can describe each joint with its position across and down the picture.')
    clip=choose_guided('pose_clip')
    index,frame=frame_slider(clip,'pose')
    mode=st.radio('View',['Original picture','Skeleton overlay','Skeleton only'],horizontal=True)
    joints={'Nose':0,'Left shoulder':5,'Right shoulder':6,'Left elbow':7,'Right elbow':8,'Left hip':11,'Right hip':12,'Left knee':13,'Right knee':14,'Left ankle':15,'Right ankle':16}
    joint_name=st.selectbox('Highlight a joint',list(joints),index=5)
    joint=joints[joint_name]
    coord=poses()[clip['id']][index]
    shown=frame if mode=='Original picture' else draw_pose(frame,coord,mode=='Skeleton only',joint)
    st.image(shown,width="stretch")
    st.caption('Teal = person A. Orange = person B. These are estimated body positions: points can be missing or misplaced, and the colours can switch between people. Some stored examples even follow the referee, the person overseeing the match, instead of an athlete.')
    for slot,offset in [('A',0),('B',34)]:
        xx,yy=coord[offset+2*joint:offset+2*joint+2]
        if 0<xx<=1 and 0<yy<=1:
            st.write(f'Player {slot}, {joint_name.lower()}: across = {xx:.3f}, down = {yy:.3f}')
        else:
            st.write(f'Player {slot}, {joint_name.lower()}: position unresolved in this frame.')
    st.caption('Across and down use fractions of the picture’s width and height. These positions are not measurements in metres.')
    st.subheader('One picture becomes a list of numbers')
    st.write('17 joints × 2 position numbers × 2 athletes = 68 numbers for one frame. The whole clip becomes 210 ordered lists, each containing 68 numbers.')
    st.markdown('**Discuss:** what useful information remains in the skeleton? What did we remove? Could grip details, camera movement or missing joints still cause problems?')
    with st.expander('Watch this skeleton sequence move'):
        st.video((DATA_DIR / 'skeletons' / f'{clip["id"]}.mp4').read_bytes(), loop=True)
        st.caption('These are the same 210 lists of body positions, drawn one after another.')
    with st.expander('The skeleton animation from the original workshop'):
        st.image(str(DATA_DIR / 'original_workshop.gif'),width=600)
        st.caption('This older animation illustrates movement as a sequence. Its frame labels and pose extraction belong to the earlier workshop task.')

elif page=='4 · Find a pattern':
    st.title('Invent your own throw detector')
    task_intro([
        'Write a simple rule describing what you would look for to spot an attempt. You can revise it as you go.',
        'Watch a practice clip and choose “Attempt” or “No attempt” before revealing its label, the supplied answer.',
        'Compare your prediction with the label. Revise your rule if needed, then use the Practice clip menu to try all four clips.',
    ], 'Trying your rule on different examples helps you discover what is useful. Your words guide your own decisions; they do not train a neural network.')
    attempt_guide()
    st.write('Watch the practice clips. Before revealing each label, decide whether it contains an attempt. Write a rule that could help someone make the same decision.')
    st.text_area('Your current rule',key='practice_rule', value=st.session_state.get('saved_practice_rule', ''),
                 on_change=remember_rule, args=('practice_rule', 'saved_practice_rule'),
                 placeholder='I think a throw attempt might involve…',height=110)
    clips=sorted((c for c in catalogue() if c['role']=='practice'), key=lambda c: c['title'])
    choice=st.selectbox('Practice clip',range(len(clips)),format_func=lambda i:clips[i]['title'])
    clip=clips[choice]
    play(clip)
    answer=st.radio('Your prediction',['Choose an answer','Attempt','No attempt'],key=f'practice_answer_{clip["id"]}',horizontal=True)
    if st.button('Reveal this practice label',key=f'reveal_{clip["id"]}'):
        if answer=='Choose an answer':st.warning('Make a prediction first.')
        else:st.session_state[f'practice_revealed_{clip["id"]}']=True
    if st.session_state.get(f'practice_revealed_{clip["id"]}'):
        label='Attempt' if clip['label'] else 'No attempt'
        st.success(f'Label: {label}') if answer==label else st.info(f'Label: {label}. What would you change in your rule?')
        st.write('A practice label can help you revise your rule. Large movement alone is not enough: people can move around and pull on each other’s clothing without trying to make the other person fall.')
        if clip['provisional']:
            st.caption('This example also includes a broadcast change or pause. Discuss how that differs from continuous fighting and why it could make a misleadingly easy negative example.')
    st.subheader('How does an RNN or LSTM do this?')
    st.write('Your rule is written in words. The real classifier instead learns numerical relationships from many labelled pose sequences. It receives the joint positions frame by frame and updates a running numerical summary.')
    st.write('An RNN maintains that summary as it reads the sequence. An LSTM adds learned controls for retaining and updating information. After the sequence, a classifier uses the summary to make one prediction about the whole clip.')
    st.info('Your written rule guides your own predictions here. Writing or changing it does not train the Judo Clipper model.')
    st.markdown('**Before the final quiz:** finish revising your rule on these practice examples. Keep the final answers unseen until you have committed your predictions.')

else:
    st.title('A final check on new examples')
    clips=[c for c in catalogue() if c['role']=='quiz']
    submitted=bool(st.session_state.get('quiz_submitted'))
    if not submitted:
        task_intro([
            'Finish your rule using the practice clips before watching these two new examples.',
            'Write your final rule below, watch both clips, and choose one prediction for each. “Attempt” means there is at least one try anywhere in that clip, even if nobody falls.',
            'Choose “Submit all predictions and reveal results” when you are ready. Both answers are required; submitting locks your predictions for this session.',
        ], 'Keeping these examples separate lets you check your rule on clips whose answers you have not already used to improve it.')
        attempt_guide()
        st.write('Once you know the answers, changing your rule to score better on these same clips would not be a fair new test.')
        st.caption('This small quiz tests your own rule. It is separate from the research model’s training, validation and test split.')
        st.text_area('Your final rule',value=st.session_state.get('saved_final_rule', st.session_state.get('saved_practice_rule','')),
                     key='final_rule', on_change=remember_rule, args=('final_rule', 'saved_final_rule'), height=100)
        with st.form('final_quiz'):
            answers={}
            for clip in clips:
                st.subheader(clip['title'])
                play(clip)
                answers[clip['id']]=st.radio(f'Prediction for {clip["title"]}',
                    ['Choose an answer','Attempt','No attempt'],key=f'quiz_answer_{clip["id"]}',horizontal=True)
            if st.form_submit_button('Submit all predictions and reveal results'):
                if any(v=='Choose an answer' for v in answers.values()):
                    st.warning('Answer every final clip before submitting.')
                else:
                    mapped={k:int(v=='Attempt') for k,v in answers.items()}
                    score,rows=score_answers(clips,mapped)
                    st.session_state['quiz_submitted']=True
                    st.session_state['quiz_rows']=rows
                    st.session_state['quiz_score']=score
                    st.rerun()
    else:
        task_intro([
            'Compare your predictions with the supplied answers below.',
            'Think of a different match you could try next, and what might make it harder to judge.',
        ], 'Two examples are a starting point for discussion. You would need many new examples to find out how reliable a rule is.')
        score=st.session_state['quiz_score']
        st.metric('Correct predictions',f'{score} / {len(clips)}')
        for row in st.session_state['quiz_rows']:
            label='Attempt' if row['label'] else 'No attempt'
            answer='Attempt' if row['answer'] else 'No attempt'
            st.write(f'**{row["clip"]}**: your answer: {answer}; label: {label}. '+('Correct.' if row['correct'] else 'Missed.'))
        st.info('A couple of examples cannot establish how reliable a detector is. Think about what made the decisions easy or difficult, including camera cuts, movement and missing pose information.')
        st.markdown('**Reflection:** how would you test the idea on a new match? Which information might the skeleton miss? Why should final test examples stay separate from examples used to improve your rule?')
        st.link_button('See the real application: Judo Clipper','https://www.judoclipper.com/')
        st.caption('Your answers and rule are kept for this session. Refreshing can clear them. No LLM account or API key is needed.')

st.divider()
navigation_buttons('bottom')

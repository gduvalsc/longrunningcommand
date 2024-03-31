from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import tempfile, os, inspect
def showcodeandrun(bloc):
    st.code(bloc)
    compiled_code = compile(bloc, "<string>", "exec")
    exec(compiled_code, globals())
    st.divider()
st.header('Streamlit and how to manage the output of long-running commands.', divider='rainbow')
st.markdown('Antoine de Saint-Exupéry, in his book "Wind, Sand and Stars" published in 1939, said: "Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away."')
st.markdown('One could apply this phrase to computer science and the art of programming: "A computer program is finished not when all functions have been implemented, but when there is nothing left to remove."')
st.markdown("Let's try to apply this principle to solve the following problem, which is extremely simple to formulate: We want to write a Python/Streamlit program that runs multiple long commands in parallel and displays the result of each one in separate areas, with the ability to view the partial result of the commands (their logs) during their execution.")
st.markdown("The problem is simple, but the solution is complex to implement! There's the issue of parallelism to solve and also the method to retrieve the log of a command during its execution and display it in a Streamlit component.")
st.markdown('To conduct our tests, we will use a small Python program that takes some time to execute using "time.sleep" and randomly generates messages on stdout and stderr.')
st.markdown('The program is the following:')
st.code("""
import time, random, sys
def f(id, loop, rand):
   for i in range(loop):
      time.sleep(rand*random.random())
      out = random.randint(0,2)
      if out == 0: print(f'My name is {id} and this is message {i} sent to stdout')
      if out == 1: print(f'My name is {id} and this is message {i} sent to stderr', file=sys.stderr)
      
f('bob', 20, 5)
""")
st.markdown('An example of run produces the following output:')
st.code("""
My name is bob and this is message 0 sent to stderr
My name is bob and this is message 1 sent to stderr
My name is bob and this is message 2 sent to stdout
My name is bob and this is message 4 sent to stderr
My name is bob and this is message 5 sent to stdout
My name is bob and this is message 9 sent to stderr
My name is bob and this is message 10 sent to stderr
My name is bob and this is message 11 sent to stdout
My name is bob and this is message 12 sent to stderr
My name is bob and this is message 13 sent to stdout
My name is bob and this is message 14 sent to stdout
My name is bob and this is message 15 sent to stderr
My name is bob and this is message 16 sent to stdout
My name is bob and this is message 17 sent to stdout
My name is bob and this is message 18 sent to stdout
""")
st.markdown('For each iteration in the loop, the program sleeps for a random duration between 0 and 5 seconds, then randomly decides whether to send a message to stdout or stderr, or not to send any message at all. And it does this 20 times (in the example).')
st.markdown('With the parameters passed to the function, the execution duration is variable but it can theoretically go up to 100 seconds (20 * 5).')
st.markdown('We will now try to write a Streamlit program that contains a button to launch this program and attempts to display the log of the program in a Streamlit component. The most suitable Streamlit component for this type of requirement is "status".')
showcodeandrun("""
import streamlit as st, pexpect

externprogram=open('/tmp/extprg.py', 'w')
externprogram.write('import time, random, sys\\n')
externprogram.write('def f(id, loop, rand):\\n')
externprogram.write('   for i in range(loop):\\n')
externprogram.write('      time.sleep(rand*random.random())\\n')
externprogram.write('      out = random.randint(0,2)\\n')
externprogram.write("      if out == 0: print(f'My name is {id} and this is message {i} sent to stdout')\\n")
externprogram.write("      if out == 1: print(f'My name is {id} and this is message {i} sent to stderr', file=sys.stderr)\\n")
externprogram.write("f(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))\\n")
externprogram.write("exit(random.randint(0,1))\\n")
externprogram.close()    

prg = st.button('Start long program', type='primary')
if prg:
    child = pexpect.spawn('python3 /tmp/extprg.py Joe 10 2', encoding='utf8')
    with st.status(f'python3 /tmp/extprg.py Joe 10 2', expanded=True) as stx:
        for line in child: st.code(line)
        child.close()
        if child.exitstatus == 0: stx.update(label="python3 /tmp/extprg.py: Complete'", state="complete", expanded=False)
        else: stx.update(label="python3 /tmp/extprg.py: Ended with errors'", state="error", expanded=False)
""")
st.markdown('Setting aside the ergonomic aspect, this initial program roughly does what we want: during the execution of the program, we can visualize what is going on with the stdout and stderr of the command, we see when the program is running and when it is finished.')
st.markdown('The main ergonomic issue is the space taken up by the result.')
st.markdown("Let's consider the following program:")
showcodeandrun("""
import streamlit as st
st.code("aaa")
st.code("bbb")
st.code("ccc")
st.code("aaa\\nbbb\\nccc")
""")
st.markdown("Calling st.code n times with a parameter is not rendered the same way as calling st.code once with the concatenation of parameters! The rendering is better with the concatenation of parameters. The problem is that if we wait until the end of execution, nothing is revealed during the program's execution.")
st.markdown('One way to improve the program (the rendering) is to modify it as follows:')
showcodeandrun("""
import streamlit as st, pexpect   

prg = st.button('Start long program', key='aaa', type='primary')
if prg:
    child = pexpect.spawn('python3 /tmp/extprg.py Joe 100 2', encoding='utf8')
    with st.status(f'python3 /tmp/extprg.py Joe 100 2', expanded=True) as stx:
        content = ''
        x = st.code('')
        for line in child: 
            x.empty()
            content += line
            x = st.code(content)
        child.close()
        if child.exitstatus == 0: stx.update(label="python3 /tmp/extprg.py: Complete'", state="complete", expanded=False)
        else: stx.update(label="python3 /tmp/extprg.py: Ended with errors'", state="error", expanded=False)
""")
st.markdown("For a program that runs for a while and only returns a few lines, the previous solution might be acceptable! However, one can doubt the efficiency of such a program if, for example, it's about doing a 'tail -f'' on a log file that contains several thousand or hundred thousand lines. In this case, clearing the component to display the entire content again for each line doesn't make sense!")
st.markdown('Another improvement over the previous program would be to limit the size of the container displaying the log:')
showcodeandrun("""
import streamlit as st, pexpect   

prg = st.button('Start long program', key='bbb', type='primary')
if prg:
    child = pexpect.spawn('python3 /tmp/extprg.py Joe 100 2', encoding='utf8')
    with st.status(f'python3 /tmp/extprg.py Joe 100 2', expanded=True) as stx:
        c = st.container(height=300)
        with c:
            content = ''
            x = st.code('')
            for line in child: 
                x.empty()
                content += line
                x = st.code(content)
        child.close()
        if child.exitstatus == 0: stx.update(label="python3 /tmp/extprg.py: Complete'", state="complete", expanded=False)
        else: stx.update(label="python3 /tmp/extprg.py: Ended with errors'", state="error", expanded=False)
""")
st.markdown('This last solution presents another difficulty, which is that the focus remains centered on the initial part of the log and not on the last updated part.')
st.markdown("Now let's try to create a program where we will attempt to execute multiple long commands in parallel and visualize their logs.")
showcodeandrun("""
import streamlit as st
def launchandview(cmd, endst):
    import pexpect
    child = pexpect.spawn(cmd, encoding='utf8')
    with st.status(cmd, expanded=True) as stx:
        c = st.container(height=300)
        with c:
            content = ''
            x = st.code('')
            for line in child: 
                x.empty()
                content += line
                x = st.code(content)
        child.close()
        if child.exitstatus == 0: stx.update(label=f"{endst}: Complete'", state="complete", expanded=False)
        else: stx.update(label=f"{endst}: Ended with errors'", state="error", expanded=False)

with st.form("example1"):
    Joe = st.checkbox("Joe")
    Averell = st.checkbox("Averell")
    prg = st.form_submit_button("Start long programs", type="primary")
if prg:
    if Joe: launchandview("python3 /tmp/extprg.py Joe 10 2", "python3 /tmp/extprg.py Joe")
    if Averell: launchandview("python3 /tmp/extprg.py Averell 10 2", "python3 /tmp/extprg.py Averell")
""")
st.markdown('Unfortunately, the programs execute sequentially; the second program starts when the first one is finished!')
st.markdown("To solve the problem, we need to introduce multiprocessing or multithreading or asyncio-like techniques in Python and see what the limitations of these technologies are in the Streamlit universe.")

st.subheader('What are the issues and solutions related to using multiprocessing or parallel processing techniques with Streamlit?', divider='rainbow')
st.subheader('os.fork')
showcodeandrun("""
import streamlit as st
import os,time

prg = st.button('Start program', type='primary', key='eee')
if prg:
    if os.fork():
        st.write(f"I'm the parent process")
    else:
        st.write(f"I'm the child process")
""")
st.markdown('There is evidently an issue with Streamlit in the child process created by os.fork().')
st.subheader('Multiprocessing')
showcodeandrun("""
import streamlit as st
def f(name):
    st.write(f"Hello! I'm {name}")
prg = st.button('Start program', type='primary', key='fff')
if prg:
    import multiprocessing
    f('Ma Dalton')
    p = multiprocessing.Process(target=f, args=('Joe',))
    p.start()
    p.join()
""")
st.markdown("We have the same issue as with os.fork: we can use Streamlit functions in the parent process but not in the child processes. In the example, the function is indeed called by the child process but the st.write instruction has no effect.")
st.markdown("To work around the issue, the result of the child process needs to be communicated to the parent, and it should be the parent itself that makes the Streamlit calls.")
showcodeandrun("""
import streamlit as st
def f(queue, name):
    queue.put(f"Hello! I'm {name}")
prg = st.button('Start program', type='primary', key='ggg')
if prg:    
    import multiprocessing, time
    queue = multiprocessing.Queue()
    f(queue, 'Ma Dalton')
    p1 = multiprocessing.Process(target=f, args=(queue, 'Joe'))
    p1.start()
    p2 = multiprocessing.Process(target=f, args=(queue, 'Averell'))
    p2.start()
    time.sleep(1)
    queue.put('EOQ')
    while True:
        x = queue.get()
        if x == 'EOQ': break
        st.write(x)
        print(x)
    queue.close()
    p1.join()
    p2.join()
""")
st.markdown('Here the program works as expected! The solution is a little bit complex: a queue must created and the interaction with Streamlit must be achieved from the main process!')
st.subheader('Asyncio')
showcodeandrun("""
import streamlit as st
import asyncio
prg = st.button('Start program', type='primary', key='hhh')
if prg:   
    async def f(timeout, name):
        await asyncio.sleep(timeout)
        st.write(f"Hello! I'm {name}")
    loop = asyncio.new_event_loop()
    tasks = [
        f(2, 'Joe'),
        f(1, 'Ma Dalton'),
        f(5, 'Averell'),
        ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
""")
st.markdown('This last approach using the asyncio module is probably the best way to proceed: Streamlit calls can be made directly from an asynchronous function that will execute a long command, and it is possible to call n functions in parallel!')
st.subheader('Conclusion', divider='rainbow')
st.markdown('The solution to our problem is as follows:')
showcodeandrun("""
import streamlit as st
async def launchandview(cmd, endst):
    import pexpect
    child = pexpect.spawn(cmd, encoding='utf8')
    with st.status(cmd, expanded=True) as stx:
        c = st.container(height=300)
        await asyncio.sleep(0)
        with c:
            content = ''
            x = st.code('')
            for line in child: 
                x.empty()
                content += line
                x = st.code(content)
                await asyncio.sleep(0)
        child.close()
        if child.exitstatus == 0: stx.update(label=f"{endst}: Complete'", state="complete", expanded=False)
        else: stx.update(label=f"{endst}: Ended with errors'", state="error", expanded=False)
        await asyncio.sleep(0)

with st.form("example2"):
    Joe = st.checkbox("Joe")
    William = st.checkbox("William")
    Jack = st.checkbox("Jack")
    Averell = st.checkbox("Averell")
    prg = st.form_submit_button("Start long programs", type="primary")
if prg:
    loop = asyncio.new_event_loop()
    tasks = []
    if Joe: tasks.append(launchandview("python3 /tmp/extprg.py Joe 10 2", "python3 /tmp/extprg.py Joe"))
    if Jack: tasks.append(launchandview("python3 /tmp/extprg.py Jack 10 2", "python3 /tmp/extprg.py Jack"))
    if William: tasks.append(launchandview("python3 /tmp/extprg.py William 10 2", "python3 /tmp/extprg.py William"))
    if Averell: tasks.append(launchandview("python3 /tmp/extprg.py Averell 10 2", "python3 /tmp/extprg.py Averell"))
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
""")
st.markdown('This latest program accomplishes what we want: being able to launch n programs in parallel and visualize their progress when they are active in separate areas.')
st.markdown('Using "asyncio" is probably the most suitable solution to solve this problem. It''s possible to use "multiprocessing", but it requires the use of queues because calls to Streamlit from a subprocess are ineffective. With the "multiprocessing" module, implementation becomes more complex.')
st.markdown('As we mentioned at the beginning, "the problem is simple but the implementation is rather complex"!')
st.markdown('There remains an issue with the technique used to display the log. On each line produced, the entire log content is re-displayed. This is suitable for programs producing a reasonable number of lines, but for programs producing thousands of lines, this is probably intolerable in terms of performance and memory usage!')
st.markdown('A Streamlit component such as st.code should have an "append" or "extend" method to add information to the component without having to recreate it entirely. But this is a topic for another discussion.')

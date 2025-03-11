import streamlit as st
from PIL import Image
import os
from crewai import Agent, Task, Crew, Process
from tools.amazontool import AmazonShoppingTool
from tools.fashiontool import DressVisionTool
from crewai_tools import FileWriterTool
from datetime import datetime
from dotenv import load_dotenv

def clear_images_directory():
    for file in os.listdir(os.path.join(os.getcwd(),"images")):
        file_path = os.path.join(os.path.join(os.getcwd(),"images"), file)
        if os.path.isfile(file_path):
            os.remove(file_path)

def agents_tasks(budget,user_preference,occasion,user_fashion_style):

    Fashion_agent = Agent(
    role="Fashion designer Analyst",
    goal="""
    Find the user typical dressing style and dressing sense. And create fashion informative summary report.""",
    backstory="""
    You are fashion designer expert with lot of professional experience. With you work you deliverd 
    outstanding results to the user's in fashion domain. You are highly skilled in finding the user 
    typical dressing style and dressing sense and creating fashion informative report, by seeing and 
    analyzing the user images.""",
    tools=[DressVisionTool()],
    llm="gpt-4o",
    verbose=True)

    Outfit_designer_agent=Agent(
    role="Outfit designer expert",
    goal="""
    Design new innovative outfits sets for the user, based on the user fashion analysis report
    provided by Fashion designer Analyst, user occasion and user preference.""",
    backstory="""
    As an expert in outfit designing domain, your unique way of working style makes you standout
    that is, first you keep user occasion in mind and perform the in-dept analysis on user fashion analysis
    report and understand it completely, and then start designing new innovative outfit sets for user.
    With this working style you designed tons of new innovative outfit sets for the user's, which turnout
    you are top 1 outfit designer expert in outfit designing domain.""",
    llm="gpt-4o",
    verbose=True)

    Amazon_shopping_agent=Agent(
    role="Amazon fashion shopping expert",
    goal="""
    Extract the inputs and pass to tool. 
    Performing shop by using tool and return tool output
    """,
    backstory="""
    As an expert in doing shopping, you helped lot of users with your work.
    Extract inputs for tool and shop items by using tool, which make you standout 
    from other experts.
    """,
    tools=[AmazonShoppingTool()],
    llm='gpt-4o',
    verbose=True)

    Ui_agent=Agent(
    role="UI designer expert",
    goal="""
    Create well organized representation of blog in markdown format for each outfit set from the 
    Amazon fashion shopping expert agent by following specified set of Requirements.""",
    backstory="""
    As an expert UI designer, you helped lot of users by creating well organized representation of 
    blog in markdown format. your key skill is analyzing the available data and creating blog
    according to the Requirements. Your highly skilled in writing markdown code for displaying 
    the availabe/provided images side by side within tabular format.
    
    """,
    llm='gpt-4o',
    verbose=True)

    content_writer_agent = Agent(
    role="Content Writer",
    goal="Write markdown content of each outfit provided by UI designer expert agent, into corresponding markdown file.",
    backstory="""A professional content writer with expertise in writing the markdown format content to files as per requirements.
    your key skill is : carefully observe the provided markdown content and make sure not to miss to write any provided markdown content into it's corresponding files.""",
    llm="gpt-4o",
    tools=[FileWriterTool()],
    verbose=True)
    #Tasks
    Fashion_task=Task(
    description=f"""Find the user typical dressing style and dressing sense.
    user provided description : {user_fashion_style} about his dressing style.""",
    expected_output="A well documented fashion informative summary report.",
    agent=Fashion_agent
    )

    Outfit_designer_task=Task(
        description=f"""
        Design 3 new innovative outfit sets for the user based on the user occasion:{occasion}, user preference:{user_preference} and user
        fashion analysis report, provided by the Fashion designer Analyst.
        Use your complete experience knowledge and intelligence for creating new innovative outfit sets.
        Keep in mind user category and desiging the new innovative outfit sets.
        Each outfit set must have following products(top, bottom, footwear, and accessories).
        Name/title for the each product should follow the structure that is(user category followed by 
        color followed by type/style followed by product name.) for example : (Men's red color polo t-shirt,
        Boy's black color slim-fit jeans, Women's green color wedding design top, Girl's white color printed pant).
        Each outfit set should be unique, no other outfit set products should match each other.
        """,
        agent=Outfit_designer_agent,
        context=[Fashion_task],
        expected_output="""
        A well structured document by display the 3 outfits sets in way i,e
        -outfit set number\n:
            - top : ?
            - bottom : ?
            - footwear : ?
            - accessories : ?
            - Brief summary about outfit set.
        """)
    
    Amazon_shopping_task=Task(
        description=f"""
        Carefully observe and extract all inputs required for the tool and pass to it.
        pass the user provide budget: {budget} to tool.
        """,
        context=[Outfit_designer_task],
        agent=Amazon_shopping_agent,
        expected_output="""
        Display tool output as it is with no enchancements.""")
    
    Ui_task=Task(
    description="""
    Create a blog in markdown format for each outfit set available in the Amazon Fashion Shopping Expert Agent output. 
    
    ** Requirements: **

    1. Blog Structure:
    * Start with Outfit Title: Create a matching title for the outfit set.
    * Add Outfit Summary: Use the value of "Brief summary about outfit set" from the Outfit Designer Expert Agent output.
    * Include Outfit Type.
    2. Outfit Type:
        * If Fashion based outfit is available and Budget based outfit is available:
            * Fashion based outfit: <total price of Fashion based outfit>
                * Format: Include Fashion based outfit product details (Top, Bottom, Footwear, Accessories) with names, URLs, prices, and reasons of(top, bottom, footwear, accessories) from the Amazon Shopping Agent output.
                * Product Images: display Fashion based outfit product images side by side within tabular format of
                rows: (image of top, image of bottom, image of footwear, image of accessories) and columns: (top,bottom,footwear,accessories)
            * Budget based outfit: <total price of Budget based outfit>
                * Format: Include Budget based outfit product details (Top, Bottom, Footwear, Accessories) with names, URLs, and prices.
                * Product Images: display Budget based outfit product images side by side within tabular format of
                rows: (image of top, image of bottom, image of footwear, image of accessories) and columns: (top,bottom,footwear,accessories)
        * If Budget based outfit is available:
            * Budget based outfit: <total price of Budget based outfit>
                * Format: Include Budget based outfit product details (Top, Bottom, Footwear, Accessories) with names, URLs, and prices.
                * Product Images: display Budget based outfit product images side by side within tabular format of
                rows: (image of top, image of bottom, image of footwear, image of accessories) and columns: (top,bottom,footwear,accessories)
        * If Non budget based outfit is available: <total price of Non budget based outfit>
            * Format: Include Non budget based outfit product details (Top, Bottom, Footwear, Accessories) with names, URLs, prices, and reasons of(top, bottom, footwear, accessories) from the Amazon Shopping Agent output.
            * Product Images: display Budget based outfit product images side by side within tabular format of
                rows: (image of top, image of bottom, image of footwear, image of accessories) and columns: (top,bottom,footwear,accessories)

    3. Mandatory Rule:
        * While writing blog, always keep in mind that, must and should display product images only under the respective 
        **Product images** section corresponding to the outfit.
    
    """,
    context=[Outfit_designer_task,Amazon_shopping_task],
    agent=Ui_agent,
    expected_output="""
     A well created markdown content for 3 outfit sets by display the 3 outfits sets in way i,e
    -outfit set number\n:
    [markdown content corresponding to outfit set]
    """)

    content_writer_task = Task(
    description="""
    write the markdown content of each outfit set provided by UI designer expert agent, into each markdown files (m1.md,m2.md,m3.md).
    Ensure that each file is written completely before moving to the next.
    if files already exist:
        Overwrite them entirely, ensuring full content is retained.
    """,
    context=[Ui_task],
    agent=content_writer_agent,
    expected_output="""
    Three markdown format files : 
    1. m1.md - markdown content corresponding to the outfit set 1
    2. m2.md - markdown content corresponding to the outfit Set 2
    3. m3.md - markdown content corresponding to the outfit Set 3
    """)

    return [Fashion_agent,Outfit_designer_agent,Amazon_shopping_agent,Ui_agent,content_writer_agent],[Fashion_task,Outfit_designer_task,Amazon_shopping_task,Ui_task,content_writer_task]

def crew(budget,user_preference,occasion,user_fashion_style):
    load_dotenv()
    agents_list,tasks_list=agents_tasks(budget,user_preference,occasion,user_fashion_style)
    crew = Crew(
    agents=agents_list,
    tasks=tasks_list,
    verbose=True,
    process=Process.sequential)

    result = crew.kickoff()
    print(result)

def clear_images_directory():
    for file in os.listdir("images"):
        file_path = os.path.join("images", file)
        if os.path.isfile(file_path):
            os.remove(file_path)

def main():

    
    if "page" not in st.session_state:
        st.session_state.page="home"    
    if "content" not in st.session_state:
        st.session_state.content=None
    if "user_name" not in st.session_state:
        st.session_state.user_name=None
    if "button_number" not in st.session_state:
        st.session_state.button_number=None
    if "back" not in st.session_state:
        st.session_state.back=1
    if "budget" not in st.session_state:
        st.session_state.budget=None
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files=None
    if "image_descriptions" not in st.session_state:
        st.session_state.image_descriptions=None
    if "preferences" not in st.session_state:
        st.session_state.preferences=None
    if "reason" not in st.session_state:
        st.session_state.reason=None

    st.title("AI-powered Your Fashion Designer")
    
    # Add 'Get Saved Data' button on the top right
    col1, col2, col3,col4 = st.columns([0.33, 0.33, 0.33,0.33])
    with col1:
        if st.button("Set Back"):
            st.session_state.page="home"
            st.session_state.back=1
            st.session_state.content=None
            st.session_state.uploaded_files=None
            st.session_state.image_descriptions=None
            st.session_state.budget=None
            st.session_state.preferences=None
            st.session_state.reason=None
            st.session_state.button_number=None
    with col2:
        if st.button("Get Saved Outfits"):
                st.session_state.page = "display"
                #st.switch_page("saved_data.py")
    with col3:
        if st.button("Clear Images"):
            clear_images_directory()
            st.session_state.page = "image"
    with col4:
        if st.button("Reset"):
            st.session_state.back=1
            st.session_state.content=None
            st.session_state.uploaded_files=None
            st.session_state.image_descriptions=None
            st.session_state.budget=None
            st.session_state.preferences=None
            st.session_state.reason=None
            st.session_state.button_number=None
    
    if st.session_state.page=="home":

        #st.title("Image Upload & User Preferences")
        # Image Upload Section
        st.write("""Hi there, this AI Tool allows you to upload images, set your budget, and specify 
                 your fashion preferences. Based on your inputs, our AI agents will analyze 
                 your style, design new outfits, shop for items within your budget, and create 
                 a well-organized blog.
                 Are you exited to explore new outfits!! Start upload your images.""")
        st.write("Make sure to click clear images button before your images upload.")
        st.header("Drop Images")
        st.session_state.uploaded_files = st.file_uploader("Upload one or more images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        
        if st.session_state.uploaded_files:
            # Clear existing images in the directory
            clear_images_directory()
            st.subheader("User Images")
            cols = st.columns(len(st.session_state.uploaded_files))  # Creating columns for side-by-side display
            rows = len(st.session_state.uploaded_files) // 3 + (1 if len(st.session_state.uploaded_files) % 3 != 0 else 0)
            for i in range(rows):
                cols = st.columns(3)
                for j, uploaded_file in enumerate(st.session_state.uploaded_files[i*3:(i+1)*3]):
                    with cols[j]:
                        image = Image.open(uploaded_file)
                        st.image(image, caption=uploaded_file.name, width=150)
                        image.save(os.path.join(os.path.join(os.getcwd(),"images"), uploaded_file.name))

        
            st.subheader("Your Fashion Description")
            st.session_state.image_descriptions = st.text_area("Give a short intro about your dressing style:", "")
        
        # User Budget Input
        st.header("Set Your Budget")
        st.session_state.budget = st.number_input("Enter your budget ($):", min_value=0, step=1)
        
        # User Preferences
        st.header("Any Preferences")
        st.session_state.preferences = st.text_area("Enter your preferences (e.g., colors, brands, style)", "")
        
        # occation
        st.header("Reason For shopping")
        st.session_state.reason = st.text_area("Enter event (e.g., Vaccation, Party, Festival, Wedding)", "")
        
        # Submit Button
        if st.button("Submit") or st.session_state.content!=None:
            st.session_state.content=1
            if not st.session_state.uploaded_files or not st.session_state.image_descriptions.strip() or st.session_state.budget == 0 or not st.session_state.preferences.strip():
                st.error("Please provide all details before clicking Submit.")
            else:
                st.write("### Summary of Details")
                if st.session_state.uploaded_files:
                    st.write(f"**Fashion Description:** {st.session_state.image_descriptions}")
                
                st.write(f"**Preference:** {st.session_state.preferences}")
                st.write(f"**Reason for shop:** {st.session_state.reason}")
                st.write(f"**Budget:** ${st.session_state.budget}")
                st.success("Your information has been submitted to our AI Agents!")
                
                if st.session_state.back:
                    with st.spinner("Designing New Outfits..."):
                        crew(st.session_state.budget,st.session_state.preferences,st.session_state.reason,st.session_state.image_descriptions)
                    st.session_state.back=None
        
                outfits=["m1.md","m2.md","m3.md"]
                for i, content in enumerate(outfits, 1):
                    result=None
                    try:
                        with open(os.path.join(os.getcwd(),content), "r", encoding="utf-8") as f:
                            result=f.read()
                    except FileNotFoundError:
                        st.error("File not found!")
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                    
                    st.write(f"### Outfit {i}")
                    st.markdown(result)

                    if st.button(f"Save outfit {i}"):
                        st.session_state.button_number=i
                        
                    if st.session_state.button_number==i:
                        st.session_state.user_name = st.text_input("Enter your name :",key=f"text_{i}")
                        if st.session_state.user_name:
                            if(os.path.exists(os.path.join(os.getcwd(),st.session_state.user_name))):
                                # Get the current timestamp
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Format: YYYYMMDD_HHMMSS
                                with open(os.path.join(os.path.join(os.getcwd(),st.session_state.user_name),f"{st.session_state.user_name}_{timestamp}.md"), "w") as f:
                                    f.write(result)
                                st.success(f"Outfit set {i} saved successfully!")
                            else:
                                os.mkdir(os.path.join(os.getcwd(),st.session_state.user_name))
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
                                with open(os.path.join(os.path.join(os.getcwd(),st.session_state.user_name),f"{st.session_state.user_name}_{timestamp}.md"), "w") as f:
                                    f.write(result)
                                st.success(f"Outfit set {i} saved successfully!")
    
    if st.session_state.page=="display":
        try:
            result=None
            st.session_state.user_name=st.text_input("Enter your name : ")
            user_dir = os.path.join(os.getcwd(), st.session_state.user_name)
            if os.path.isdir(user_dir):
                files = os.listdir(user_dir)
                st.write("Saved Outfits...")
                for i in files:
                    with open(os.path.join(user_dir,i),'r') as fp:
                        r=fp.read()
                    st.markdown(r)
            else:
                st.write(f"Not found any saved list under your name : {st.session_state.user_name}")
        except Exception as e :
            print(e)

    if st.session_state.page=="image":
        st.success("Images cleared succesfully from the imagges director...")


if __name__ == "__main__":
    main()

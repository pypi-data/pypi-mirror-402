"""Gallery of classification masks b/w stain normalized and original output."""

import os

import streamlit as st


def paginator(slide_dir, dst, item_per_page=10):
    """Lets the user paginate a set of items.

    Parameters
    ----------
    label : Path of the datasets.
    dst : Path where selected image type will be saved.
        The items to display in the paginator.
    items_per_page : int
        The number of items to display per page.
    """
    dataset = os.listdir(slide_dir)
    st.markdown(
        "Green: Benign_lymphocytes, Red: Malignant_lymphocytes, Yellow: Other",
        unsafe_allow_html=True,
    )

    slides = st.sidebar.selectbox("Select dataset", dataset)
    slide_level_folders = os.listdir(os.path.join(slide_dir, slides))
    select_slides = st.selectbox("Select slide_uuid", slide_level_folders)
    select_folder_path = os.path.join(slide_dir, slides, select_slides)
    image_files = [f for f in os.listdir(select_folder_path)]
    start_idx = 0
    end_idx = len(image_files)

    for i in range(start_idx, end_idx):
        text_name = image_files[i].split(".")[0]
        image_path = os.path.join(select_folder_path, image_files[i])
        st.image(image_path, caption=image_files[i], use_column_width=True)
        file_name = os.path.join(dst, f"{text_name}.txt")
        select = st.radio(
            f"Image {i + 1}",
            ["Not selected", "Original", "Stain-normalized"],
            key=text_name,
        )
        if select == "Original" or select == "Stain-normalized":
            st.write("selected:", select)
            with open(file_name, "w") as file:
                file.write(f"{text_name}, {select}")


slide_dir = "/gstore/scratch/dp_labs/data/inference_stain_norm_2/"
dst = "/gstore/scratch/dp_labs/data/inference_stain_norm_pathologists/"
paginator(slide_dir, dst, item_per_page=10)

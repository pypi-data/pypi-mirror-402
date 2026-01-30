import os

import streamlit as st
import streamlit.components.v1 as components


_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        "st_gridtable",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_gridtable", path=build_dir)



def st_gridtable(
    columns,
    data,
    titleKey,
    imageKey,
    badgeKeys,
    detailKeys,
    cardSize=280,
    cardGap=16,
    fontSize=14,
    fontColor="rgba(0, 0, 0, .6)",
    pageSize=20,
    pageSizeOptions=[10,20,50,100],
    initialPage=0,
    key=None
    ):
    
    component_value = _component_func(
        columns=columns,
    data=data,
    titleKey=titleKey,
    imageKey=imageKey,
    badgeKeys=badgeKeys,
    detailKeys=detailKeys,
    cardSize=cardSize,
    cardGap=cardGap,
    fontSize=fontSize,
    fontColor=fontColor,
    pageSize=pageSize,
    pageSizeOptions=pageSizeOptions,
    initialPage=initialPage,
    key=None
)
    return component_value

    
# return_value = st_gridtable({})

# # st.write("Number of clicks:", return_value)
# st.write("You selected:", return_value)
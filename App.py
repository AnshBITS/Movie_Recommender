import streamlit as st
from PIL import Image
import json
from Classifier import KNearestNeighbours
from bs4 import BeautifulSoup
import requests, io
import PIL.Image

# Load movie data and titles
with open('./Data/movie_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open('./Data/movie_titles.json', 'r', encoding='utf-8') as f:
    movie_titles = json.load(f)

# Correct User-Agent Header
hdr = {'User-Agent': 'Mozilla/5.0'}

def movie_poster_fetcher(imdb_link):
    """Fetch and display Movie Poster."""
    try:
        url_data = requests.get(imdb_link, headers=hdr, timeout=5).text
        s_data = BeautifulSoup(url_data, 'html.parser')
        imdb_dp = s_data.find("meta", property="og:image")

        if imdb_dp and 'content' in imdb_dp.attrs:
            movie_poster_link = imdb_dp['content']
        else:
            movie_poster_link = "https://via.placeholder.com/158x301?text=No+Poster"

        response = requests.get(movie_poster_link, stream=True, timeout=5)
        image = PIL.Image.open(io.BytesIO(response.content))
        image = image.resize((158, 301))
        st.image(image, use_container_width=False)

    except Exception as e:
        st.warning(f"Error fetching movie poster: {e}")
        st.image("https://via.placeholder.com/158x301?text=Error", use_container_width=False)

def get_movie_info(imdb_link):
    """Fetch movie director, cast, story, and rating."""
    try:
        url_data = requests.get(imdb_link, headers=hdr, timeout=5).text
        s_data = BeautifulSoup(url_data, 'html.parser')

        # Fetch description
        imdb_content = s_data.find("meta", property="og:description")
        if imdb_content and 'content' in imdb_content.attrs:
            description = imdb_content['content']
            parts = description.split('.')

            movie_director = parts[0].strip() if len(parts) > 0 else "Director not available"
            movie_cast = parts[1].replace('With', 'Cast: ').strip() if len(parts) > 1 else "Cast not available"
            movie_story = 'Story: ' + parts[2].strip() + '.' if len(parts) > 2 else "Story not available."
        else:
            movie_director = "Director not available"
            movie_cast = "Cast not available"
            movie_story = "Story not available."

        # Fetch Rating
        rating_tag = s_data.find("span", {"class": "sc-7ab21ed2-1 jGRxWM"})  # Updated class for rating
        if rating_tag:
            movie_rating = 'IMDb Rating: ' + rating_tag.text + ' ⭐'
        else:
            movie_rating = "IMDb Rating: Not available."

        return movie_director, movie_cast, movie_story, movie_rating

    except Exception as e:
        st.warning(f"Error fetching movie information: {e}")
        return "Director not available", "Cast not available", "Story not available.", "IMDb Rating: Not available."

def KNN_Movie_Recommender(test_point, k):
    """Recommend movies using KNN."""
    target = [0 for item in movie_titles]
    model = KNearestNeighbours(data, target, test_point, k=k)
    model.fit()
    table = []
    for i in model.indices:
        table.append([movie_titles[i][0], movie_titles[i][2], data[i][-1]])
    return table

st.set_page_config(
    page_title="Movie Recommender System",
)

def run():
    img1 = Image.open('./meta/logo.jpg')
    img1 = img1.resize((250, 250))
    st.image(img1, use_container_width=False)
    st.title("Movie Recommender System")
    st.markdown(
        '''<h4 style='text-align: left; color: #d73b5c;'>* Data is based on "IMDB 5000 Movie Dataset"</h4>''',
        unsafe_allow_html=True
    )

    genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
              'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News',
              'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']

    movies = [title[0] for title in movie_titles]
    category = ['--Select--', 'Movie based', 'Genre based']

    cat_op = st.selectbox('Select Recommendation Type', category)

    if cat_op == category[0]:
        st.warning('Please select Recommendation Type!!')

    elif cat_op == category[1]:  # Movie based
        select_movie = st.selectbox('Select movie:', ['--Select--'] + movies)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))

        if select_movie == '--Select--':
            st.warning('Please select a Movie!!')
        else:
            no_of_reco = st.slider('Number of movies you want Recommended:', min_value=5, max_value=20, step=1)
            genres_vector = data[movies.index(select_movie)]
            test_points = genres_vector
            table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
            table.pop(0)
            c = 0
            st.success('Recommended movies:')
            for movie, link, ratings in table:
                c += 1
                st.markdown(f"({c}) [**{movie}**]({link})")
                if dec == 'Yes':
                    movie_poster_fetcher(link)
                director, cast, story, movie_rating = get_movie_info(link)
                st.markdown(director)
                st.markdown(cast)
                st.markdown(story)
                st.markdown(movie_rating)
                st.markdown('Recommender Score: ' + str(ratings) + ' ⭐')

    elif cat_op == category[2]:  # Genre based
        sel_gen = st.multiselect('Select Genres:', genres)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))

        if sel_gen:
            imdb_score = st.slider('Choose IMDb score:', 1, 10, 8)
            no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)
            test_point = [1 if genre in sel_gen else 0 for genre in genres]
            test_point.append(imdb_score)
            table = KNN_Movie_Recommender(test_point, no_of_reco)
            c = 0
            st.success('Recommended movies:')
            for movie, link, ratings in table:
                c += 1
                st.markdown(f"({c}) [**{movie}**]({link})")
                if dec == 'Yes':
                    movie_poster_fetcher(link)
                director, cast, story, movie_rating = get_movie_info(link)
                st.markdown(director)
                st.markdown(cast)
                st.markdown(story)
                st.markdown(movie_rating)
                st.markdown('Recommender Score: ' + str(ratings) + ' ⭐')

run()

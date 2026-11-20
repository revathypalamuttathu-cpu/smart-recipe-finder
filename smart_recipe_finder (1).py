import streamlit as st
import requests
import random
from urllib.parse import quote

# ------------------------------------------------------------
# SMART RECIPE FINDER
# Run: streamlit run smart_recipe_finder.py
# ------------------------------------------------------------

st.set_page_config(
    page_title="Smart Recipe Finder",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "https://www.themealdb.com/api/json/v1/1"

# A small offline starter collection. Online searches use TheMealDB's
# much larger public recipe catalogue.
SAMPLE_RECIPES = [
    {
        "idMeal": "local1", "strMeal": "Vegetable Fried Rice",
        "strCategory": "Vegetarian", "strArea": "Asian",
        "strMealThumb": "", "strTags": "Quick, Rice",
        "strInstructions": "1. Cook the rice and let it cool.\\n2. Heat oil in a pan.\\n3. Add chopped vegetables and stir-fry.\\n4. Add rice, soy sauce, salt and pepper.\\n5. Toss well and serve hot.",
        "ingredients": ["Rice", "Carrot", "Beans", "Spring onion", "Soy sauce", "Oil"]
    },
    {
        "idMeal": "local2", "strMeal": "Classic Pancakes",
        "strCategory": "Dessert", "strArea": "American",
        "strMealThumb": "", "strTags": "Breakfast, Sweet",
        "strInstructions": "1. Mix flour, milk, egg, sugar and baking powder.\\n2. Whisk into a smooth batter.\\n3. Pour small portions onto a warm greased pan.\\n4. Flip when bubbles appear.\\n5. Serve with fruit or syrup.",
        "ingredients": ["Flour", "Milk", "Egg", "Sugar", "Baking powder"]
    },
    {
        "idMeal": "local3", "strMeal": "Tomato Pasta",
        "strCategory": "Vegetarian", "strArea": "Italian",
        "strMealThumb": "", "strTags": "Pasta, Dinner",
        "strInstructions": "1. Boil pasta until tender.\\n2. Sauté garlic in olive oil.\\n3. Add chopped tomatoes and seasoning.\\n4. Simmer until saucy.\\n5. Mix in pasta and garnish with herbs.",
        "ingredients": ["Pasta", "Tomato", "Garlic", "Olive oil", "Basil"]
    },
    {
        "idMeal": "local4", "strMeal": "Chicken Curry",
        "strCategory": "Chicken", "strArea": "Indian",
        "strMealThumb": "", "strTags": "Spicy, Dinner",
        "strInstructions": "1. Sauté onion, ginger and garlic.\\n2. Add curry spices and tomatoes.\\n3. Add chicken pieces and stir.\\n4. Add water and simmer until chicken is fully cooked.\\n5. Finish with coriander and serve.",
        "ingredients": ["Chicken", "Onion", "Tomato", "Ginger", "Garlic", "Curry powder"]
    },
    {
        "idMeal": "local5", "strMeal": "Fresh Fruit Salad",
        "strCategory": "Vegetarian", "strArea": "International",
        "strMealThumb": "", "strTags": "Healthy, Dessert",
        "strInstructions": "1. Wash and chop seasonal fruits.\\n2. Combine in a bowl.\\n3. Add a little lemon juice or honey if desired.\\n4. Chill and serve fresh.",
        "ingredients": ["Apple", "Banana", "Orange", "Grapes", "Lemon"]
    },
    {
        "idMeal": "local6", "strMeal": "Masala Omelette",
        "strCategory": "Breakfast", "strArea": "Indian",
        "strMealThumb": "", "strTags": "Quick, Breakfast",
        "strInstructions": "1. Beat eggs in a bowl.\\n2. Mix in chopped onion, tomato, chilli and coriander.\\n3. Season with salt and pepper.\\n4. Cook in a lightly oiled pan on both sides.\\n5. Serve warm.",
        "ingredients": ["Egg", "Onion", "Tomato", "Green chilli", "Coriander"]
    }
]


def api_get(endpoint, params=None):
    """Safely call TheMealDB. Return None if the service is unavailable."""
    try:
        response = requests.get(
            f"{API}/{endpoint}",
            params=params,
            timeout=8,
            headers={"User-Agent": "SmartRecipeFinder/1.0"}
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def ingredients_for(meal):
    if meal.get("ingredients"):
        return meal["ingredients"]
    items = []
    for i in range(1, 21):
        ingredient = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if ingredient:
            items.append(f"{measure} {ingredient}".strip())
    return items


def get_recipes(search_term="", ingredient=""):
    """Search online recipes, with local examples as an offline fallback."""
    if ingredient.strip():
        data = api_get("filter.php", {"i": ingredient.strip()})
        meals = (data or {}).get("meals") or []
        if meals:
            # Fetch full details for the first few ingredient matches.
            detailed = []
            for meal in meals[:18]:
                full = api_get("lookup.php", {"i": meal["idMeal"]})
                result = (full or {}).get("meals") or []
                if result:
                    detailed.append(result[0])
            if detailed:
                return detailed

    if search_term.strip():
        data = api_get("search.php", {"s": search_term.strip()})
        meals = (data or {}).get("meals") or []
        if meals:
            return meals
        return [
            r for r in SAMPLE_RECIPES
            if search_term.lower() in r["strMeal"].lower()
            or search_term.lower() in r["strArea"].lower()
            or search_term.lower() in r["strCategory"].lower()
        ]

    data = api_get("search.php", {"s": ""})
    meals = (data or {}).get("meals") or []
    return meals if meals else SAMPLE_RECIPES


def get_categories():
    data = api_get("list.php", {"c": "list"})
    return [x["strCategory"] for x in (data or {}).get("meals", [])]


def get_areas():
    data = api_get("list.php", {"a": "list"})
    return [x["strArea"] for x in (data or {}).get("meals", [])]


def get_recipe_details(meal):
    if str(meal.get("idMeal", "")).startswith("local"):
        return meal
    data = api_get("lookup.php", {"i": meal.get("idMeal")})
    result = (data or {}).get("meals") or []
    return result[0] if result else meal


def matches_filters(meal, category, area, diet):
    meal_category = (meal.get("strCategory") or "").lower()
    meal_area = (meal.get("strArea") or "").lower()
    ingredients = " ".join(ingredients_for(meal)).lower()

    if category != "All categories" and category.lower() not in meal_category:
        return False
    if area != "All cuisines" and area.lower() not in meal_area:
        return False
    if diet == "Vegetarian":
        non_veg = ["chicken", "beef", "pork", "fish", "shrimp", "lamb", "turkey", "bacon", "duck"]
        if any(word in ingredients for word in non_veg):
            return False
    elif diet == "Non-vegetarian":
        non_veg = ["chicken", "beef", "pork", "fish", "shrimp", "lamb", "turkey", "bacon", "duck"]
        if not any(word in ingredients for word in non_veg):
            return False
    return True


# ---------------------------- Styling ----------------------------

st.markdown("""
<style>
    .stApp { background: #fbfaf7; }
    .main-title { font-size: 2.65rem; font-weight: 850; color: #20352b; margin-bottom: 0; }
    .subtitle { color: #68766d; font-size: 1.05rem; margin-top: 4px; }
    .hero {
        padding: 1.5rem 1.7rem; border-radius: 20px;
        background: linear-gradient(115deg, #e6f1e8, #fff0dc);
        margin: 1rem 0 1.5rem 0;
    }
    .recipe-name { font-size: 1.08rem; font-weight: 750; color: #26392f; }
    .small-muted { color: #758078; font-size: .9rem; }
    div.stButton > button {
        border-radius: 10px; border: 1px solid #d5e1d7;
        background: #ffffff; color: #254b35; font-weight: 650;
    }
    div.stButton > button:hover { border-color: #548c64; color: #183d27; }
    [data-testid="stSidebar"] { background: #f0f4ef; }
</style>
""", unsafe_allow_html=True)

if "favorites" not in st.session_state:
    st.session_state.favorites = {}
if "selected_recipe" not in st.session_state:
    st.session_state.selected_recipe = None
if "last_results" not in st.session_state:
    st.session_state.last_results = SAMPLE_RECIPES


# ---------------------------- Sidebar ----------------------------

with st.sidebar:
    st.markdown("## 🍳 Smart Recipe Finder")
    st.caption("Your little kitchen companion")
    page = st.radio(
        "Navigation",
        ["🏠 Discover", "❤️ My Favourites", "🎲 Surprise Me", "ℹ️ About"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("### Refine your recipes")

    category_options = ["All categories"] + get_categories()
    area_options = ["All cuisines"] + get_areas()

    category = st.selectbox("Food category", category_options)
    area = st.selectbox("Cuisine", area_options)
    diet = st.selectbox("Food preference", ["All", "Vegetarian", "Non-vegetarian"])
    st.caption("Filters are applied to the recipes currently displayed.")


# ---------------------------- Recipe detail view ----------------------------

def show_recipe(meal):
    details = get_recipe_details(meal)
    st.markdown("---")
    if st.button("← Back to recipes"):
        st.session_state.selected_recipe = None
        st.rerun()

    st.title(details.get("strMeal", "Recipe"))
    image_url = details.get("strMealThumb")
    if image_url:
        st.image(image_url, width=520)

    c1, c2, c3 = st.columns(3)
    c1.metric("Cuisine", details.get("strArea") or "Various")
    c2.metric("Category", details.get("strCategory") or "Recipe")
    c3.metric("Ingredients", len(ingredients_for(details)))

    if details.get("strYoutube"):
        st.link_button("▶ Watch recipe video", details["strYoutube"])

    left, right = st.columns([1, 1.5])
    with left:
        st.subheader("🧺 Ingredients")
        for item in ingredients_for(details):
            st.markdown(f"- {item}")
    with right:
        st.subheader("👩‍🍳 Cooking instructions")
        instructions = details.get("strInstructions") or "Instructions are not available."
        for paragraph in instructions.replace("\r", "").split("\n"):
            if paragraph.strip():
                st.write(paragraph.strip())

    if details.get("strSource"):
        st.markdown(f"[Original recipe source]({details['strSource']})")

    recipe_id = str(details.get("idMeal"))
    if st.button("❤️ Save to favourites", key=f"save_{recipe_id}"):
        st.session_state.favorites[recipe_id] = details
        st.success("Recipe saved to My Favourites!")


# ---------------------------- Main pages ----------------------------

st.markdown('<div class="main-title">🍽️ Smart Recipe Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Discover something delicious with the ingredients you have.</div>', unsafe_allow_html=True)

if st.session_state.selected_recipe:
    show_recipe(st.session_state.selected_recipe)

elif page == "🏠 Discover":
    st.markdown("""
    <div class="hero">
      <h2 style="color:#244633;margin:0;">What would you like to cook today?</h2>
      <p style="color:#5c6e61;margin-bottom:0;">Search thousands of recipes, explore cuisines, and find inspiration for your next meal.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("recipe_search_form"):
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔎 Search by recipe name", placeholder="e.g. pasta, biryani, soup...")
        with col2:
            ingredient = st.text_input("🥕 I have this ingredient", placeholder="e.g. chicken, potato...")
        submitted = st.form_submit_button("Find recipes", use_container_width=True)

    if submitted or "search_done" not in st.session_state:
        if submitted:
            st.session_state.search_done = True
            st.session_state.last_results = get_recipes(search_term, ingredient)
        elif "search_done" not in st.session_state:
            st.session_state.last_results = get_recipes()

    recipes = st.session_state.last_results
    recipes = [r for r in recipes if matches_filters(r, category, area, diet)]

    st.subheader(f"✨ Recipes for you ({len(recipes)})")
    if not recipes:
        st.info("No recipes matched those filters. Try another ingredient, cuisine or category.")
    else:
        for start in range(0, len(recipes), 3):
            cols = st.columns(3)
            for col, meal in zip(cols, recipes[start:start + 3]):
                with col:
                    with st.container(border=True):
                        if meal.get("strMealThumb"):
                            st.image(meal["strMealThumb"], use_container_width=True)
                        else:
                            st.markdown("### 🍲")
                        st.markdown(f'<div class="recipe-name">{meal.get("strMeal", "Recipe")}</div>', unsafe_allow_html=True)
                        st.caption(f"{meal.get('strArea') or 'Various'} • {meal.get('strCategory') or 'Recipe'}")
                        rid = str(meal.get("idMeal"))
                        if st.button("View recipe →", key=f"view_{rid}", use_container_width=True):
                            st.session_state.selected_recipe = meal
                            st.rerun()
                        if st.button("♡ Save", key=f"fav_{rid}", use_container_width=True):
                            st.session_state.favorites[rid] = meal
                            st.toast("Added to favourites!")

elif page == "❤️ My Favourites":
    st.subheader("❤️ My Favourite Recipes")
    if not st.session_state.favorites:
        st.info("You haven't saved any recipes yet. Explore recipes and tap ♡ Save.")
    else:
        for meal in st.session_state.favorites.values():
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1:
                if meal.get("strMealThumb"):
                    st.image(meal["strMealThumb"], use_container_width=True)
                else:
                    st.markdown("🍲")
            with c2:
                st.markdown(f"**{meal.get('strMeal', 'Recipe')}**")
                st.caption(f"{meal.get('strArea') or 'Various'} • {meal.get('strCategory') or 'Recipe'}")
            with c3:
                rid = str(meal.get("idMeal"))
                if st.button("View", key=f"favview_{rid}"):
                    st.session_state.selected_recipe = meal
                    st.rerun()
                if st.button("Remove", key=f"remove_{rid}"):
                    st.session_state.favorites.pop(rid, None)
                    st.rerun()
            st.divider()

elif page == "🎲 Surprise Me":
    st.subheader("🎲 Let the app choose your next meal!")
    if st.button("Surprise me with a recipe", type="primary"):
        data = api_get("random.php")
        meals = (data or {}).get("meals") or []
        if meals:
            st.session_state.selected_recipe = meals[0]
            st.rerun()
        else:
            st.session_state.selected_recipe = random.choice(SAMPLE_RECIPES)
            st.rerun()
    st.caption("You might discover a new favourite!")

elif page == "ℹ️ About":
    st.subheader("About Smart Recipe Finder")
    st.write(
        "Smart Recipe Finder is a recipe discovery application built with Python and Streamlit. "
        "It helps users search recipes, explore cuisines, filter food preferences, view ingredients "
        "and instructions, and save favourite meals."
    )
    st.markdown("**Main technologies**")
    st.markdown("- Python – application logic")
    st.markdown("- Streamlit – interactive application interface")
    st.markdown("- Requests – online recipe data")
    st.markdown("- TheMealDB – public recipe database and API")
    st.info("An internet connection is needed for the full online recipe catalogue. A small sample collection is included as a fallback.")

st.markdown("---")
st.caption("Smart Recipe Finder • Made with Python and Streamlit • Recipe data powered by TheMealDB")

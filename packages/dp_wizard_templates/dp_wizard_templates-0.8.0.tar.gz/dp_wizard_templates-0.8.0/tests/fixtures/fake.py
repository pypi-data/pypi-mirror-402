# `pip install` output should be stripped:

# +
# %pip install pytest
# -

# Should be markdown (implicit)

# + [markdown]
# Should be markdown (explicit)
# -

# + [markdown] tags=["my_css_class"]
# Should be markdown (tags)
# -

# +

# Should be code

print("2 + 2")

# -

# + tags=["my_css_class"]

# Should be code (tags)

print(2 + 2)

# -

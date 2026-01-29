import pytest
from dotpath import __version__, getpath, setpath

pets_dic = {
    "pets": {
        "dog": {
            "name": "Billy",
            "age": 5,
            "friends": ["Joe", "Jack"],
        },
        "cat": {
            "name": "Joe",
            "age": 6,
            "friends": ["Billy", "Pop"],
        },
    },
}


def test_named_path_dic():
    """Test to get a path from dot specification."""
    dog_name_dic = getpath(pets_dic, "pets.dog.name")
    dog_friend_dic = getpath(pets_dic, "pets.dog.friends.0")
    cat_name_dic = getpath(pets_dic, "pets.cat.name")
    cat_friend_dic = getpath(pets_dic, "pets.cat.friends.1")
    assert dog_name_dic == "Billy", f"Value was {dog_name_dic}, should be Billy."
    assert dog_friend_dic == "Joe", f"Value was {dog_name_dic}, should be Joe."
    assert cat_name_dic == "Joe", f"Value was {cat_name_dic}, should be Joe."
    assert cat_friend_dic == "Pop", f"Value was {cat_name_dic}, should be Pop."


def test_default_value_dic():
    """Test to get default value when not found."""
    default_dog_name_dic = getpath(pets_dic, "pets.dog.no_name", "Jorge")
    default_cat_name_dic = getpath(pets_dic, "pets.cat.no_name", "Felix")
    assert default_dog_name_dic == "Jorge", (
        f"Value was {default_dog_name_dic}, should be Jorge."
    )
    assert default_cat_name_dic == "Felix", (
        f"Value was {default_cat_name_dic}, should be Felix."
    )


def test_exeption_dic():
    """Test to raise exception when indexes not found."""
    with pytest.raises((AttributeError, KeyError, IndexError)):
        getpath(pets_dic, "pets.cat.excep_name", raise_exception=True)

    with pytest.raises((AttributeError, KeyError, IndexError)):
        getpath(pets_dic, "pets.dog.excep_name", raise_exception=True)


class PetObj:
    def __init__(self, name, age):
        self.name = name
        self.age = age


class PetsObj:
    pets = {}

    def add_pet(self, pet_index, pet):
        self.pets[pet_index] = pet


pets_obj = PetsObj()
pets_obj.add_pet("dog", PetObj("Billy", 5))
pets_obj.add_pet("cat", PetObj("Joe", 6))


def test_named_path_obj():
    """Test to get a path from dot specification."""
    dog_name_obj = getpath(pets_obj, "pets.dog.name")
    cat_name_obj = getpath(pets_obj, "pets.cat.name")
    assert dog_name_obj == "Billy", f"Value was {dog_name_obj}, should be Billy."
    assert cat_name_obj == "Joe", f"Value was {cat_name_obj}, should be Joe."


def test_default_value_obj():
    """Test to get default value when not found."""
    default_dog_name_obj = getpath(pets_obj, "pets.dog.no_name", "Jorge")
    default_cat_name_obj = getpath(pets_obj, "pets.cat.no_name", "Felix")
    assert default_dog_name_obj == "Jorge", (
        f"Value was {default_dog_name_obj}, should be Jorge."
    )
    assert default_cat_name_obj == "Felix", (
        f"Value was {default_cat_name_obj}, should be Felix."
    )


def test_exeption_obj():
    """Test to raise exception when indexes not found."""
    with pytest.raises((AttributeError, KeyError, IndexError)):
        getpath(pets_obj, "pets.cat.excep_name", raise_exception=True)

    with pytest.raises((AttributeError, KeyError, IndexError)):
        getpath(pets_obj, "pets.dog.excep_name", raise_exception=True)


def test_setpath_dict_creates_children():
    """Test setting a value in a dict using dotpath."""
    data = {}
    setpath(data, "pets.dog.name", "Billy")
    assert data["pets"]["dog"]["name"] == "Billy"


def test_setpath_list_expands():
    """Test setting a value inside a list index."""
    data = {"pets": {"dog": {"friends": []}}}
    setpath(data, "pets.dog.friends.1", "Joe")
    assert data["pets"]["dog"]["friends"] == [None, "Joe"]


def test_setpath_object_creates_attributes():
    """Test setting a value on an object via dotpath."""

    class PetStore:
        pass

    store = PetStore()
    setpath(store, "pets.dog.name", "Billy")
    assert store.pets["dog"]["name"] == "Billy"


def test_setpath_no_create_returns_default():
    """Test setpath behavior when not creating missing children."""
    data = {}
    result = setpath(data, "pets.dog.name", "Billy", default=False, create_child=False)
    assert result is False

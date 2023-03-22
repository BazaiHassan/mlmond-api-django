"""
Serializer for dataset APIs
"""

from rest_framework import serializers

from core.models import Dataset, Tag, Ingredient

class DatasetImageSerializer(serializers.ModelSerializer):
    """ Serializer to uploading image to the dataset """

    class Meta:
        model = Dataset
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image':{'required':'True'}}

class IngredientSerializer(serializers.ModelSerializer):
    """ serializer for ingredient """
    class Meta:
        model = Ingredient
        fields = ['id','name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for tags """
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields=['id']


class DatasetSerializer(serializers.ModelSerializer):
    """ serializer for datasets """
    tags = TagSerializer(many = True, required = False)
    ingredients = IngredientSerializer(many = True, required=False)
    image = serializers.ImageField(max_length=None, use_url=True)
    class Meta:
        model = Dataset
        fields = ['id','title','time_minutes','price','link','tags','ingredients']
        read_only_fields = ['id']


    def _get_or_create_tags(self, tags, dataset):
        """ Handle getting or creating tag as needed """
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(user = auth_user, **tag,)
            dataset.tags.add(tag_obj)

        return dataset

    def _get_or_create_ingredients(self, ingredients, dataset):
        """ Handle getting or creating ingredient as needed """
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(user = auth_user, **ingredient,)
            dataset.ingredients.add(ingredient_obj)

        return dataset
        

    def create(self, validated_data):
        """ Create a dataset """
        tags = validated_data.pop('tags',[])
        ingredients = validated_data.pop('ingredients',[])
        dataset = Dataset.objects.create(**validated_data)
        self._get_or_create_tags(tags, dataset)
        self._get_or_create_ingredients(ingredients, dataset)
        return dataset



    def update(self, instance, validated_data):
        """ Update the dataset """
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class DatasetDetailSerializer(DatasetSerializer):
    """ Serializer for dataset detail view """
    
    class Meta(DatasetSerializer.Meta):
        fields = DatasetSerializer.Meta.fields + ['description','image']

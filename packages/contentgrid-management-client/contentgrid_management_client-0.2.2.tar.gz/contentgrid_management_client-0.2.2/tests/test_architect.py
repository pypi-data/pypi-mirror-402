from urllib.parse import urlparse
from pytest import fixture, raises, skip
from contentgrid_hal_client.hal import HALFormsClient
from contentgrid_hal_client.exceptions import NotFound
from contentgrid_management_client.console import (
    Blueprint, EntityDefinition, AttributeType, AttributeDefinition,
    ConstraintType, SearchType, get_blueprint
)
from tests.management_testcontainers import *


class TestBluePrintOperations:
    """Test Blueprint operations including entity and attribute management."""
    
    blueprint: Blueprint = None
    
    @classmethod
    @fixture(autouse=True)
    def setup_blueprint(cls, gateway_with_auth):
        """Set up the blueprint once for all tests in this class."""
        parsed_url = urlparse(gateway_with_auth['blueprint_url'])
        client_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        client = HALFormsClient(client_endpoint=client_endpoint, token=gateway_with_auth['access_token'])
        cls.blueprint = get_blueprint(blueprint_url=gateway_with_auth['blueprint_url'], hal_client=client)
        
        yield cls.blueprint
    
    def test_get_entity_definitions(self):
        """Test retrieving entity definitions from blueprint."""
        entity_definitions = self.blueprint.get_entity_definitions()
        assert isinstance(entity_definitions, list)
        for entity in entity_definitions:
            assert isinstance(entity, EntityDefinition)
            assert hasattr(entity, 'name')
            assert hasattr(entity, 'description')
    
    def test_create_and_delete_entity(self):
        """Test creating and deleting an entity definition."""
        entity = self.blueprint.create_entity("test-entity", entity_description="A test entity")
        assert entity.name == "test-entity"
        assert entity.description == "A test entity"
        assert isinstance(entity.attribute_definitions, list)
        assert isinstance(entity.relation_definitions, list)
        
        entity.delete()
        with raises(NotFound):
            self.blueprint.get_entity_definition_by_name("test-entity")
    
    def test_get_entity_by_name(self):
        """Test retrieving an entity by name."""
        entity = self.blueprint.create_entity("lookup-entity", entity_description="Entity for lookup test")
        
        found_entity = self.blueprint.get_entity_definition_by_name("lookup-entity")
        assert found_entity.name == entity.name
        assert found_entity.description == entity.description
        
        entity.delete()
    
    def test_get_nonexistent_entity_raises_error(self):
        """Test that getting a non-existent entity raises NotFound."""
        with raises(NotFound):
            self.blueprint.get_entity_definition_by_name("nonexistent-entity")
    
    def test_patch_entity(self):
        """Test updating entity properties."""
        entity = self.blueprint.create_entity("patch-entity", entity_description="Original description")
        
        entity.patch(new_entity_description="Updated description")
        entity.refetch()
        assert entity.description == "Updated description"
        
        entity.patch(new_entity_name="renamed-entity")
        entity.refetch()
        assert entity.name == "renamed-entity"
        
        entity.delete()


class TestAttributeOperations:
    """Test attribute creation and management."""
    
    blueprint: Blueprint = None
    test_entity: EntityDefinition = None
    
    @classmethod
    @fixture(autouse=True)
    def setup_entity(cls, gateway_with_auth):
        """Set up entity for attribute tests."""
        parsed_url = urlparse(gateway_with_auth['blueprint_url'])
        client_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        client = HALFormsClient(client_endpoint=client_endpoint, token=gateway_with_auth['access_token'])
        cls.blueprint = get_blueprint(blueprint_url=gateway_with_auth['blueprint_url'], hal_client=client)
        cls.test_entity = cls.blueprint.create_entity("attribute-test-entity", entity_description="Entity for attribute tests")
        
        yield cls.test_entity
        
        cls.test_entity.delete()
    
    def test_create_string_attribute(self):
        """Test creating a STRING type attribute."""
        attr = self.test_entity.create_attribute("text_field", AttributeType.STRING, attribute_description="Text field")
        assert attr.name == "text_field"
        assert attr.type == AttributeType.STRING
        assert attr.description == "Text field"
        assert attr.natural_id == False
    
    def test_create_numeric_attributes(self):
        """Test creating numeric type attributes."""
        long_attr = self.test_entity.create_attribute("count", AttributeType.LONG, attribute_description="Count field")
        assert long_attr.type == AttributeType.LONG
        
        double_attr = self.test_entity.create_attribute("price", AttributeType.DOUBLE, attribute_description="Price field")
        assert double_attr.type == AttributeType.DOUBLE
    
    def test_create_boolean_attribute(self):
        """Test creating a BOOLEAN type attribute."""
        attr = self.test_entity.create_attribute("is_active", AttributeType.BOOLEAN, attribute_description="Active flag")
        assert attr.type == AttributeType.BOOLEAN
    
    def test_create_date_attributes(self):
        """Test creating date/datetime type attributes."""
        date_attr = self.test_entity.create_attribute("birth_date", AttributeType.DATE, attribute_description="Birth date")
        assert date_attr.type == AttributeType.DATE
        
        datetime_attr = self.test_entity.create_attribute("created_at", AttributeType.DATETIME, attribute_description="Creation timestamp")
        assert datetime_attr.type == AttributeType.DATETIME
    
    def test_create_natural_id_attribute(self):
        """Test creating an attribute as natural ID."""
        attr = self.test_entity.create_attribute("user_id", AttributeType.STRING, attribute_description="User ID", natural_id=True)
        assert attr.natural_id == True
    
    def test_get_attribute_by_name(self):
        """Test retrieving an attribute by name."""
        created_attr = self.test_entity.create_attribute("lookup_field", AttributeType.STRING, attribute_description="Lookup test")
        self.test_entity.refetch()
        
        found_attr = self.test_entity.get_attribute_definition_by_name("lookup_field")
        assert found_attr.name == created_attr.name
        assert found_attr.type == created_attr.type
    
    def test_get_nonexistent_attribute_raises_error(self):
        """Test that getting a non-existent attribute raises NotFound."""
        with raises(NotFound):
            self.test_entity.get_attribute_definition_by_name("nonexistent_field")
    
    def test_patch_attribute(self):
        """Test updating attribute properties."""
        attr = self.test_entity.create_attribute("patch_field", AttributeType.STRING, attribute_description="Original")
        
        attr.patch(attribute_description="Updated description")
        attr.refetch()
        assert attr.description == "Updated description"
        
        attr.patch(attribute_name="renamed_field")
        attr.refetch()
        assert attr.name == "renamed_field"


class TestAttributeConstraints:
    """Test attribute constraints (required, unique, allowed values)."""
    
    blueprint: Blueprint = None
    test_entity: EntityDefinition = None
    
    @classmethod
    @fixture(autouse=True)
    def setup_entity(cls, gateway_with_auth):
        """Set up entity for constraint tests."""
        parsed_url = urlparse(gateway_with_auth['blueprint_url'])
        client_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        client = HALFormsClient(client_endpoint=client_endpoint, token=gateway_with_auth['access_token'])
        cls.blueprint = get_blueprint(blueprint_url=gateway_with_auth['blueprint_url'], hal_client=client)
        cls.test_entity = cls.blueprint.create_entity("constraint-test-entity", entity_description="Entity for constraint tests")
        
        yield cls.test_entity
        
        cls.test_entity.delete()
    
    def test_enable_required_constraint(self):
        """Test enabling required constraint on an attribute."""
        attr = self.test_entity.create_attribute("required_field", AttributeType.STRING, attribute_description="Required field")
        attr.enable_required_constraint()
        attr.refetch()
        
        constraints = attr.get_constraints_of_type(ConstraintType.REQUIRED)
        assert len(constraints) == 1
        assert constraints[0].type == ConstraintType.REQUIRED
    
    def test_enable_unique_constraint(self):
        """Test enabling unique constraint on an attribute."""
        attr = self.test_entity.create_attribute("unique_field", AttributeType.STRING, attribute_description="Unique field")
        attr.enable_unique_constraint()
        attr.refetch()
        
        constraints = attr.get_constraints_of_type(ConstraintType.UNIQUE)
        assert len(constraints) == 1
        assert constraints[0].type == ConstraintType.UNIQUE
    
    def test_add_allowed_values_constraint(self):
        """Test adding allowed values constraint to an attribute."""
        attr = self.test_entity.create_attribute("status", AttributeType.STRING, attribute_description="Status field")
        allowed_values = ["active", "inactive", "pending"]
        
        constraint = attr.add_allowed_values_constraint(allowed_values)
        attr.refetch()
        
        constraints = attr.get_constraints_of_type(ConstraintType.ALLOWED_VALUES)
        assert len(constraints) == 1
        assert constraints[0].type == ConstraintType.ALLOWED_VALUES
        assert set(constraints[0].values) == set(allowed_values)
    
    def test_update_allowed_values(self):
        """Test updating allowed values in an existing constraint."""
        attr = self.test_entity.create_attribute("category", AttributeType.STRING, attribute_description="Category field")
        initial_values = ["cat1", "cat2"]
        attr.add_allowed_values_constraint(initial_values)
        attr.refetch()
        
        # Get the constraint and update it
        constraints = attr.get_constraints_of_type(ConstraintType.ALLOWED_VALUES)
        assert len(constraints) == 1
        
        new_values = ["cat1", "cat2", "cat3", "cat4"]
        constraints[0].update_values(new_values)
        constraints[0].refetch()
        
        assert set(constraints[0].values) == set(new_values)
    
    def test_multiple_constraints_on_attribute(self):
        """Test that an attribute can have multiple constraints."""
        attr = self.test_entity.create_attribute("multi_constraint", AttributeType.STRING, attribute_description="Field with multiple constraints")
        
        attr.enable_required_constraint()
        attr.enable_unique_constraint()
        attr.add_allowed_values_constraint(["value1", "value2", "value3"])
        attr.refetch()
        
        all_constraints = attr.get_constraints()
        assert len(all_constraints) == 3
        
        constraint_types = {c.type for c in all_constraints}
        assert ConstraintType.REQUIRED in constraint_types
        assert ConstraintType.UNIQUE in constraint_types
        assert ConstraintType.ALLOWED_VALUES in constraint_types


class TestAttributeSearchOptions:
    """Test attribute search options (exact, prefix)."""
    
    blueprint: Blueprint = None
    test_entity: EntityDefinition = None
    
    @classmethod
    @fixture(autouse=True)
    def setup_entity(cls, gateway_with_auth):
        """Set up entity for search option tests."""
        parsed_url = urlparse(gateway_with_auth['blueprint_url'])
        client_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        client = HALFormsClient(client_endpoint=client_endpoint, token=gateway_with_auth['access_token'])
        cls.blueprint = get_blueprint(blueprint_url=gateway_with_auth['blueprint_url'], hal_client=client)
        cls.test_entity = cls.blueprint.create_entity("search-test-entity", entity_description="Entity for search tests")
        
        yield cls.test_entity
        
        cls.test_entity.delete()
    
    def test_enable_exact_search(self):
        """Test enabling exact search on an attribute."""
        attr = self.test_entity.create_attribute("exact_search_field", AttributeType.STRING, attribute_description="Exact search field")
        attr.enable_exact_search()
        attr.refetch()
        
        search_options = attr.get_search_options_of_type(SearchType.EXACT)
        assert len(search_options) == 1
        assert search_options[0].type == SearchType.EXACT
    
    def test_enable_prefix_search(self):
        """Test enabling prefix search on an attribute."""
        attr = self.test_entity.create_attribute("prefix_search_field", AttributeType.STRING, attribute_description="Prefix search field")
        attr.enable_prefix_search()
        attr.refetch()
        
        search_options = attr.get_search_options_of_type(SearchType.PREFIX)
        assert len(search_options) == 1
        assert search_options[0].type == SearchType.PREFIX
    
    def test_multiple_search_options(self):
        """Test that an attribute can have both exact and prefix search."""
        attr = self.test_entity.create_attribute("multi_search", AttributeType.STRING, attribute_description="Multiple search options")
        
        attr.enable_exact_search()
        attr.enable_prefix_search()
        attr.refetch()
        
        all_search_options = attr.get_search_options()
        assert len(all_search_options) == 2
        
        search_types = {opt.type for opt in all_search_options}
        assert SearchType.EXACT in search_types
        assert SearchType.PREFIX in search_types


class TestRelationOperations:
    """Test relation creation and management."""
    
    blueprint: Blueprint = None
    source_entity: EntityDefinition = None
    target_entity: EntityDefinition = None
    
    @classmethod
    @fixture(autouse=True)
    def setup_entities(cls, gateway_with_auth):
        """Set up entities for relation tests."""
        parsed_url = urlparse(gateway_with_auth['blueprint_url'])
        client_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        client = HALFormsClient(client_endpoint=client_endpoint, token=gateway_with_auth['access_token'])
        cls.blueprint = get_blueprint(blueprint_url=gateway_with_auth['blueprint_url'], hal_client=client)
        cls.source_entity = cls.blueprint.create_entity("relation-source", entity_description="Source entity for relations")
        cls.target_entity = cls.blueprint.create_entity("relation-target", entity_description="Target entity for relations")
        
        yield
        
        cls.source_entity.delete()
        cls.target_entity.delete()
    
    def test_create_one_to_many_relation(self):
        """Test creating a one-to-many relation."""
        relation = self.source_entity.create_relation(
            relation_name="has_targets",
            target=self.target_entity.name,
            many_source_per_target=False,
            many_target_per_source=True,
            relation_description="One source to many targets"
        )
        
        assert relation.name == "has_targets"
        assert relation.source == self.source_entity.name
        assert relation.target == self.target_entity.name
        assert relation.many_source_per_target == False
        assert relation.many_target_per_source == True
        assert relation.required == False
    
    def test_create_many_to_one_relation(self):
        """Test creating a many-to-one relation."""
        relation = self.source_entity.create_relation(
            relation_name="belongs_to",
            target=self.target_entity.name,
            many_source_per_target=True,
            many_target_per_source=False,
            relation_description="Many sources to one target"
        )
        
        assert relation.many_source_per_target == True
        assert relation.many_target_per_source == False
    
    def test_create_many_to_many_relation(self):
        """Test creating a many-to-many relation."""
        relation = self.source_entity.create_relation(
            relation_name="related_to",
            target=self.target_entity.name,
            many_source_per_target=True,
            many_target_per_source=True,
            relation_description="Many to many"
        )
        
        assert relation.many_source_per_target == True
        assert relation.many_target_per_source == True
    
    def test_create_required_relation(self):
        """Test creating a required relation."""
        relation = self.source_entity.create_relation(
            relation_name="required_relation",
            target=self.target_entity.name,
            many_source_per_target=False,
            many_target_per_source=False,
            required=True
        )
        
        assert relation.required == True
    
    def test_get_relation_by_name(self):
        """Test retrieving a relation by name."""
        created_relation = self.source_entity.create_relation(
            relation_name="lookup_relation",
            target=self.target_entity.name,
            many_source_per_target=False,
            many_target_per_source=True
        )
        self.source_entity.refetch()
        
        found_relation = self.source_entity.get_relation_definition_by_name("lookup_relation")
        assert found_relation.name == created_relation.name
        assert found_relation.target == created_relation.target
    
    def test_get_nonexistent_relation_raises_error(self):
        """Test that getting a non-existent relation raises NotFound."""
        with raises(NotFound):
            self.source_entity.get_relation_definition_by_name("nonexistent-relation")
    
    def test_patch_relation(self):
        """Test updating relation properties."""
        relation = self.source_entity.create_relation(
            relation_name="patch_relation",
            target=self.target_entity.name,
            many_source_per_target=False,
            many_target_per_source=True,
            relation_description="Original description"
        )
        
        relation.patch(new_relation_description="Updated description")
        relation.refetch()
        assert relation.description == "Updated description"
        
        relation.patch(new_relation_name="renamed_relation")
        relation.refetch()
        assert relation.name == "renamed_relation"
    
    def test_create_bidirectional_relation(self):
        """Test creating a bidirectional relation with inverse."""
        relation = self.source_entity.create_relation(
            relation_name="owns",
            target=self.target_entity.name,
            many_source_per_target=False,
            many_target_per_source=True,
            inverse_relation_name="owned_by",
            relation_description="Owner relation"
        )
        
        assert relation.name == "owns"
        assert relation.inverse_name == "owned_by"
        assert relation.is_bidirectional() == True
        assert relation.primary_side == True
        assert relation.required == False
        assert relation.inverse_required == False

    
    def test_get_inverse_relation(self):
        """Test retrieving the inverse relation from a bidirectional relation."""
        relation = self.source_entity.create_relation(
            relation_name="manages",
            target=self.target_entity.name,
            many_source_per_target=True,
            many_target_per_source=False,
            inverse_relation_name="managed_by"
        )
        
        inverse = relation.get_inverse_relation()
        assert inverse is not None
        assert inverse.name == "managed_by"
        assert inverse.source == self.target_entity.name
        assert inverse.target == self.source_entity.name
        assert inverse.primary_side == False
        assert inverse.is_bidirectional() == True
        
        # Test that inverse of inverse points back to original
        inverse_of_inverse = inverse.get_inverse_relation()
        assert inverse_of_inverse is not None
        assert inverse_of_inverse.name == "manages"
    
    def test_unidirectional_relation_has_no_inverse(self):
        """Test that unidirectional relations return None for inverse."""
        relation = self.source_entity.create_relation(
            relation_name="references",
            target=self.target_entity.name,
            many_source_per_target=True,
            many_target_per_source=True
        )
        
        assert relation.is_bidirectional() == False
        assert relation.inverse_name is None
        assert relation.get_inverse_relation() is None
    
    def test_patch_inverse_relation_name(self):
        """Test updating the inverse relation name."""
        relation = self.source_entity.create_relation(
            relation_name="created_by",
            target=self.target_entity.name,
            many_source_per_target=True,
            many_target_per_source=True,
            inverse_relation_name="creates"
        )
        
        relation.patch(new_inverse_relation_name="created")
        relation.refetch()
        assert relation.inverse_name == "created"
        
        # Verify inverse side also updated
        inverse = relation.get_inverse_relation()
        assert inverse is not None
        assert inverse.name == "created"
    
    def test_bidirectional_relation_to_dict(self):
        """Test that bidirectional relations serialize correctly."""
        relation = self.source_entity.create_relation(
            relation_name="approves",
            target=self.target_entity.name,
            many_source_per_target=False,
            many_target_per_source=True,
            inverse_relation_name="approved_by",
            required=False,
            inverse_required=False
        )
        
        relation_dict = relation.to_dict()
        assert relation_dict["name"] == "approves"
        assert relation_dict["is_bidirectional"] == True
        assert relation_dict["inverse_name"] == "approved_by"
        assert relation_dict["required"] == False
        assert relation_dict["inverse_required"] == False
    
    def test_unidirectional_relation_to_dict(self):
        """Test that unidirectional relations serialize correctly without inverse fields."""
        relation = self.source_entity.create_relation(
            relation_name="links_to",
            target=self.target_entity.name,
            many_source_per_target=True,
            many_target_per_source=True
        )
        
        relation_dict = relation.to_dict()
        assert relation_dict["name"] == "links_to"
        assert relation_dict["is_bidirectional"] == False
        assert "inverse_name" not in relation_dict
        assert "inverse_required" not in relation_dict


class TestAutomationOperations:
    """Test automation creation and annotation management."""
    
    blueprint: Blueprint = None
    test_entity: EntityDefinition = None
    
    @classmethod
    @fixture(autouse=True)
    def setup_entity(cls, gateway_with_auth):
        """Set up entity for automation tests."""
        parsed_url = urlparse(gateway_with_auth['blueprint_url'])
        client_endpoint = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
        client = HALFormsClient(client_endpoint=client_endpoint, token=gateway_with_auth['access_token'])
        cls.blueprint = get_blueprint(blueprint_url=gateway_with_auth['blueprint_url'], hal_client=client)
        cls.test_entity = cls.blueprint.create_entity("automation-test-entity", entity_description="Entity for automation tests")
        cls.test_entity.create_attribute("test_field", AttributeType.STRING, attribute_description="Test field")
        
        yield cls.test_entity
        
        cls.test_entity.delete()
    
    def test_create_automation(self):
        """Test creating an automation."""
        automation = self.blueprint.create_automation(
            automation_name="test-automation",
            system_name="test-system",
            automation_data={"key": "value"}
        )
        
        assert automation.name == "test-automation"
        assert automation.system == "test-system"
        assert automation.automation_data == {"key": "value"}
        assert hasattr(automation, 'id')
    
    def test_get_automations(self):
        """Test retrieving automations from blueprint."""
        automation = self.blueprint.create_automation(
            automation_name="list-test-automation",
            system_name="test-system",
            automation_data={}
        )
        
        automations = self.blueprint.get_automations()
        assert isinstance(automations, list)
        assert any(a.name == "list-test-automation" for a in automations)
    
    def test_create_annotation_on_entity(self):
        """Test creating an annotation on an entity."""
        skip("Returns 403 by architect")
        automation = self.blueprint.create_automation(
            automation_name="entity-annotation-test",
            system_name="test-system",
            automation_data={}
        )
        
        annotation = automation.create_annotation_on_entity(
            entity_name=self.test_entity.name,
            data={"annotation_key": "annotation_value"}
        )
        
        assert annotation.subject.type.name == "ENTITY"
        assert annotation.subject.entity == self.test_entity.name
        assert annotation.annotation_data == {"annotation_key": "annotation_value"}
    
    def test_create_annotation_on_attribute(self):
        """Test creating an annotation on an attribute."""
        skip("Returns 403 by architect")
        automation = self.blueprint.create_automation(
            automation_name="attribute-annotation-test",
            system_name="test-system",
            automation_data={}
        )
        
        annotation = automation.create_annotation_on_attribute(
            entity_name=self.test_entity.name,
            attribute_name="test_field",
            data={"attr_annotation": "value"}
        )
        
        assert annotation.subject.type.name == "ATTRIBUTE"
        assert annotation.subject.entity == self.test_entity.name
        assert annotation.subject.attribute == "test_field"
        assert annotation.annotation_data == {"attr_annotation": "value"}
    
    def test_get_annotations(self):
        """Test retrieving annotations from an automation."""
        skip("Returns 403 by architect")
        automation = self.blueprint.create_automation(
            automation_name="annotations-list-test",
            system_name="test-system",
            automation_data={}
        )
        
        automation.create_annotation_on_entity(
            entity_name=self.test_entity.name,
            data={"test": "data"}
        )
        
        annotations = automation.get_annotations()
        assert isinstance(annotations, list)
        assert len(annotations) >= 1
    
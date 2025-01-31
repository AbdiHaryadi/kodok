from dataclasses import dataclass
from entities import ObjectSpecification, QuestionAnswer

def ds_confidence(lower_bound: float, upper_bound: float):
    return (lower_bound + upper_bound) / 2

@dataclass
class DempsterShaferGuess:
    content: str
    lower_bound: float
    upper_bound: float

    def get_content(self):
        return self.content
    
    def get_confidence(self):
        return ds_confidence(self.lower_bound, self.upper_bound)

class DempsterShaferDomain:
    def __and__(self, other: "DempsterShaferDomain") -> "DempsterShaferDomain":
        raise NotImplementedError
    
    def __hash__(self):
        raise NotImplementedError
    
    def __eq__(self, other: "DempsterShaferDomain"):
        raise NotImplementedError
    
class AllDempsterShaferDomain(DempsterShaferDomain):
    def __and__(self, other):
        return other
    
    def __hash__(self):
        return hash("[all]")
    
    def __eq__(self, other):
        return isinstance(other, AllDempsterShaferDomain)

class EmptyDempsterShaferDomain(DempsterShaferDomain):
    def __and__(self, other):
        return self
    
    def __hash__(self):
        return hash("[none]")
    
    def __eq__(self, other):
        return isinstance(other, EmptyDempsterShaferDomain)

class SinglePositiveDempsterShaferDomain(DempsterShaferDomain):
    def __init__(self, key: str):
        self.key = key

    def __and__(self, other):
        if isinstance(other, SinglePositiveDempsterShaferDomain):
            if self.key == other.key:
                return self
            else:
                return EmptyDempsterShaferDomain()
            
        return other & self
    
    def __hash__(self):
        return hash(self.key)
    
    def __eq__(self, other):
        if isinstance(other, SinglePositiveDempsterShaferDomain):
            return self.key == other.key

        return False

class DempsterShaferQAGuesser:
    ALL_KEY = "[all]"

    def __init__(
            self,
            object_spec_list: list[ObjectSpecification]
    ):
        self.object_spec_list = object_spec_list
        self._validate_object_specificaton_list()

        self.mass_map = {
            AllDempsterShaferDomain(): 1.0
        }

    def _validate_object_specificaton_list(self):
        object_spec_list = self.object_spec_list
        n_object_spec = len(object_spec_list)
        if n_object_spec == 0:
            raise ValueError("Object specification list is empty")
        
        object_name_set: set[str] = set()
        illegal_name = DempsterShaferQAGuesser.ALL_KEY
        for obj_spec in object_spec_list:
            obj_name = obj_spec.name
            if obj_name == illegal_name:
                raise ValueError(f"Illegal object specification name: {obj_name}")

            if obj_name in object_name_set:
                raise ValueError(f"Duplicate object specification with name \"{obj_name}\"")
            
            object_name_set.add(obj_name)

    def update(self, qa: QuestionAnswer) -> None:
        chosen_obj_spec: ObjectSpecification | None = None
        for obj_spec in self.object_spec_list:
            for obj_question in obj_spec.positive_questions:
                if obj_question == qa.question and qa.answer == True:
                    chosen_obj_spec = obj_spec
        
        if chosen_obj_spec is None:
            raise ValueError
        
        factor_mass_map: dict[DempsterShaferDomain, float] = {
            SinglePositiveDempsterShaferDomain(chosen_obj_spec.name): 0.9,
            AllDempsterShaferDomain(): 0.1,
        }

        # TODO: Buatkan kelas baru
        new_mass_map: dict[DempsterShaferDomain, float] = {}

        for old_domain, old_mass in self.mass_map.items():
            for factor_domain, factor_mass in factor_mass_map.items():
                if isinstance(old_domain, AllDempsterShaferDomain):
                    if factor_domain not in new_mass_map:
                        new_mass_map[factor_domain] = 0.0

                    new_mass_map[factor_domain] += old_mass * factor_mass
                
                else:
                    raise NotImplementedError
                
        self.mass_map = new_mass_map

    def guess(self):
        obj_name = self.object_spec_list[0].name
        lower_bound = self.mass_map.get(SinglePositiveDempsterShaferDomain(obj_name), 0.0)
        upper_bound = lower_bound + self.mass_map[AllDempsterShaferDomain()]

        return DempsterShaferGuess(
            content=obj_name,
            lower_bound=lower_bound,
            upper_bound=upper_bound
        )

# Tests
def test_no_update():
    object_spec_list = [
        ObjectSpecification(
            name="Demam Berdarah Dengue (DBD)",
            positive_questions=[
                "Demam?",
                "Demam mendadak yang tinggi?",
                "Suhu demam hingga 39 derajat Celcius?",
                "Nyeri kepala?",
                "Menggigil?",
            ]
        ),
        ObjectSpecification(
            name="Tipus",
            positive_questions=[
                "Demam?",
                "Demam berlangsung lebih dari seminggu?",
                "Kelelahan yang berlebihan?",
                "Nyeri kepala?",
            ]
        ),
    ]
    guesser = DempsterShaferQAGuesser(object_spec_list)
    g = guesser.guess()
    content = g.get_content()
    confidence = g.get_confidence()
    assert any((content == x.name for x in object_spec_list))

    expected_confidence = ds_confidence(0.0, 1.0)
    assert confidence == expected_confidence, f"Expecting {expected_confidence}, got {confidence}"

def test_duplicate():
    object_spec_list = [
        ObjectSpecification(
            name="Demam Berdarah Dengue (DBD)",
            positive_questions=[
                "Demam?",
            ]
        ),
        ObjectSpecification(
            name="Demam Berdarah Dengue (DBD)",
            positive_questions=[
                "Demam?",
                "Demam mendadak yang tinggi?",
            ]
        ),
    ]
    try:
        DempsterShaferQAGuesser(object_spec_list)
        assert False
    except ValueError as e:
        assert str(e).startswith("Duplicate object specification with name")

def test_empty_list():
    object_spec_list = []
    try:
        DempsterShaferQAGuesser(object_spec_list)
        assert False
    except ValueError as e:
        assert str(e).startswith("Object specification list is empty")

def test_illegal_name():
    illegal_name = DempsterShaferQAGuesser.ALL_KEY
    object_spec_list = [
        ObjectSpecification(
            name=illegal_name,
            positive_questions=[
                "Demam?",
            ]
        )
    ]
    try:
        DempsterShaferQAGuesser(object_spec_list)
        assert False
    except ValueError as e:
        assert str(e) == f"Illegal object specification name: {illegal_name}"

def test_single_update():
    object_spec_list = [
        ObjectSpecification(
            name="A",
            positive_questions=["ap1"]
        ),
        ObjectSpecification(
            name="B",
            positive_questions=["bp2"]
        )
    ]

    guesser = DempsterShaferQAGuesser(object_spec_list)
    guesser.update(QuestionAnswer(
        question="ap1",
        answer=True
    ))
    g = guesser.guess()
    content = g.get_content()
    assert content == "A", f"Unexpected, got \"{content}\""

    confidence = g.get_confidence()
    expected_confidence = ds_confidence(0.9, 1.0)
    assert confidence == expected_confidence, f"Expecting {expected_confidence}, got {confidence}"

def test_single_update_2():
    object_spec_list = [
        ObjectSpecification(
            name="A",
            positive_questions=["ap1"]
        ),
        ObjectSpecification(
            name="B",
            positive_questions=["bp2"]
        )
    ]

    guesser = DempsterShaferQAGuesser(object_spec_list)
    guesser.update(QuestionAnswer(
        question="ap1",
        answer=False
    ))
    g = guesser.guess()
    content = g.get_content()
    assert content == "A", f"Unexpected, got \"{content}\""

    confidence = g.get_confidence()
    expected_confidence = ds_confidence(0.0, 0.1)
    assert confidence == expected_confidence, f"Expecting {expected_confidence}, got {confidence}"

if __name__ == "__main__":
    test_no_update()
    test_duplicate()
    test_empty_list()
    test_illegal_name()
    test_single_update()
    # test_single_update_2()
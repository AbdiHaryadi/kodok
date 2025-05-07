from dataclasses import dataclass, field
import json
from typing import Optional


@dataclass
class QuestionTree:
    questions: dict[str, "QuestionTree"] = field(default_factory=dict)
    groups: dict[str, dict[str, "QuestionTree"]] = field(default_factory=dict)
    parent: Optional["QuestionTree"] = None
    
    @staticmethod
    def load(path: str) -> "QuestionTree":
        with open(path) as fp:
            data = json.load(fp)

        question_branches = data.get("question_branches", [])
        group_branches = data.get("group_branches", [])
        group_questions_data = data.get("group_questions", [])

        question_texts = data.get("general_questions", [])
        group_texts = data.get("general_groups", [])

        return QuestionTree.build_question_tree_with_given_texts(question_branches, group_branches, group_questions_data, question_texts, group_texts)

    @staticmethod
    def build_question_tree(
            question_branches: list[dict[str, str]],
            group_branches: list[dict[str, str]],
            group_questions_data: list[dict[str, str]],
            parent_question_text: str
    ) -> "QuestionTree":
        question_texts = [x["child_question"] for x in question_branches if x["question"] == parent_question_text]
        group_texts = [x["group"] for x in group_branches if x["question"] == parent_question_text]

        return QuestionTree.build_question_tree_with_given_texts(question_branches, group_branches, group_questions_data, question_texts, group_texts)
    
    @staticmethod
    def build_question_tree_with_given_texts(
            question_branches: list[dict[str, str]],
            group_branches: list[dict[str, str]],
            group_questions_data: list[dict[str, str]],
            question_texts: list[str],
            group_texts: list[str]
    ) -> "QuestionTree":
        questions = QuestionTree.build_questions(question_branches, group_branches, group_questions_data, question_texts)       
        groups = QuestionTree.build_groups(question_branches, group_branches, group_questions_data, group_texts)
        
        result = QuestionTree(questions=questions, groups=groups)
        for v in questions.values():
            v.parent = result

        for v in groups.values():
            for v2 in v.values():
                v2.parent = result

        return result
    
    @staticmethod
    def build_questions(
            question_branches: list[dict[str, str]],
            group_branches: list[dict[str, str]],
            group_questions_data: list[dict[str, str]],
            question_texts: list[str]
    ):
        questions = {}
        for text in question_texts:
            questions[text] = QuestionTree.build_question_tree(question_branches, group_branches, group_questions_data, text)

        return questions
    
    @staticmethod
    def build_groups(
            question_branches: list[dict[str, str]],
            group_branches: list[dict[str, str]],
            group_questions_data: list[dict[str, str]],
            group_texts: list[str]
    ):
        groups = {}
        for text in group_texts:
            group_question_texts = [x["question"] for x in group_questions_data if x["group"] == text]
            groups[text] = QuestionTree.build_questions(question_branches, group_branches, group_questions_data, group_question_texts)

        return groups
    
    def get_subtree(self, question: str) -> Optional["QuestionTree"]:
        for q, v in self.questions.items():
            if q == question:
                return v
            
            subtree_result = v.get_subtree(question)
            if subtree_result is not None:
                return subtree_result
            
        for gv in self.groups.values():
            for q, v in gv.items():
                if q == question:
                    return v
                
                subtree_result = v.get_subtree(question)
                if subtree_result is not None:
                    return subtree_result
        
        return None
    
    def get_question_path(self, question: str) -> Optional[list[str]]:
        for q, v in self.questions.items():
            if q == question:
                return [q]
            
            subtree_result = v.get_question_path(question)
            if subtree_result is not None:
                return [q] + subtree_result
            
        for gv in self.groups.values():
            for q, v in gv.items():
                if q == question:
                    return [q]
                
                subtree_result = v.get_question_path(question)
                if subtree_result is not None:
                    return [q] + subtree_result
        
        return None
    
    def get_questions_by_group(self, group: str) -> list[str]:
        for q, v in self.questions.items():
            subtree_result = v.get_questions_by_group(group)
            if len(subtree_result) > 0:
                return subtree_result
            
        for g, gv in self.groups.items():
            if g == group:
                return [q for q in gv.keys()]
            
            for q, v in gv.items():
                subtree_result = v.get_questions_by_group(group)
                if len(subtree_result) > 0:
                    return subtree_result
        
        return []
# logic_engine.py
# Practical 07: Knowledge Base + Forward Chaining Inference Engine


class KnowledgeBase:
    """Declarative KB storing Facts (percepts) and Rules (Horn clauses)."""

    def __init__(self):
        self.facts = set()   # unique fact strings, e.g. 'TargetVisible'
        self.rules = []      # tuples: (premise_list, conclusion_string)

    def tell_fact(self, fact_string):
        self.facts.add(fact_string)

    def tell_rule(self, premise_list, conclusion_string):
        self.rules.append((list(premise_list), conclusion_string))

    def clear_facts(self):
        self.facts.clear()

    def forward_chain(self):
        """Data-driven forward chaining.

        Keeps sweeping over the rules until a full pass adds no new fact
        (a fixed point is reached).
        """
        new_facts_added = True

        while new_facts_added:
            new_facts_added = False

            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    # Modus Ponens: all premises known  =>  conclusion holds
                    if all(p in self.facts for p in premises):
                        self.facts.add(conclusion)
                        new_facts_added = True

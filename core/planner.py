"""
Meal-Based Planner: creates optimal supplement schedule around meals
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

class MealTime(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"

@dataclass
class SupplementSlot:
    supplement_id: str
    name: str
    timing: str  # "before", "with", "after"
    notes: str = ""

@dataclass
class MealPlan:
    meal: MealTime
    display_name: str
    before: List[SupplementSlot] = field(default_factory=list)
    with_meal: List[SupplementSlot] = field(default_factory=list)
    after: List[SupplementSlot] = field(default_factory=list)

class MealPlanner:
    def __init__(self, catalog: dict, constraints: List[dict] = None):
        self.catalog = catalog
        self.constraints = constraints or []
        
        # Define meal timing preferences
        self.meal_display = {
            MealTime.BREAKFAST: "🍳 Сніданок",
            MealTime.LUNCH: "🍽 Обід",
            MealTime.DINNER: "🌙 Вечеря"
        }
    
    def create_plan(self, selected_supplements: List[str]) -> Dict[MealTime, MealPlan]:
        """
        Create meal-based plan for selected supplements.
        Considers:
        - Optimal time (morning/evening)
        - With/without food requirements
        - Separation constraints from compatibility check
        """
        plans = {
            MealTime.BREAKFAST: MealPlan(MealTime.BREAKFAST, self.meal_display[MealTime.BREAKFAST]),
            MealTime.LUNCH: MealPlan(MealTime.LUNCH, self.meal_display[MealTime.LUNCH]),
            MealTime.DINNER: MealPlan(MealTime.DINNER, self.meal_display[MealTime.DINNER])
        }
        
        # Get supplements that need separation
        separation_pairs = self._get_separation_pairs()
        
        for supp_id in selected_supplements:
            supp = self.catalog.get(supp_id)
            if not supp:
                continue
            
            timing = supp.get('timing', {})
            best_time = timing.get('best_time', 'any')
            with_food = timing.get('with_food', True)
            notes = timing.get('notes', '')
            
            slot = SupplementSlot(
                supplement_id=supp_id,
                name=supp['name'],
                timing="with" if with_food else "before",
                notes=notes
            )
            
            # Determine which meal(s) to assign
            target_meal = self._determine_meal(supp_id, best_time, separation_pairs, plans)
            
            if with_food:
                plans[target_meal].with_meal.append(slot)
            else:
                plans[target_meal].before.append(slot)
        
        return plans
    
    def _get_separation_pairs(self) -> List[tuple]:
        """Extract supplement pairs that need separation"""
        pairs = []
        for c in self.constraints:
            if c.get('type') == 'separate':
                pairs.append(tuple(c['supplements']))
        return pairs
    
    def _determine_meal(self, supp_id: str, best_time: str, 
                        separation_pairs: List[tuple], 
                        current_plans: Dict[MealTime, MealPlan]) -> MealTime:
        """Determine best meal for supplement considering constraints"""
        
        # Default preferences based on best_time
        if best_time == 'morning':
            preferred = [MealTime.BREAKFAST, MealTime.LUNCH, MealTime.DINNER]
        elif best_time == 'evening':
            preferred = [MealTime.DINNER, MealTime.LUNCH, MealTime.BREAKFAST]
        else:
            preferred = [MealTime.BREAKFAST, MealTime.LUNCH, MealTime.DINNER]
        
        # Check separation constraints
        for meal in preferred:
            assigned = self._get_assigned_supplements(current_plans[meal])
            conflicts = False
            
            for pair in separation_pairs:
                if supp_id in pair:
                    other = pair[0] if pair[1] == supp_id else pair[1]
                    if other in assigned:
                        conflicts = True
                        break
            
            if not conflicts:
                return meal
        
        # If all have conflicts, return first preferred (will need manual adjustment)
        return preferred[0]
    
    def _get_assigned_supplements(self, plan: MealPlan) -> List[str]:
        """Get list of supplement IDs already assigned to a meal"""
        assigned = []
        for slot in plan.before + plan.with_meal + plan.after:
            assigned.append(slot.supplement_id)
        return assigned
    
    def format_plan(self, plans: Dict[MealTime, MealPlan]) -> str:
        """Format complete plan for display"""
        lines = ["📅 *План прийому БАДів*\n"]
        
        for meal_time in [MealTime.BREAKFAST, MealTime.LUNCH, MealTime.DINNER]:
            plan = plans[meal_time]
            has_supplements = plan.before or plan.with_meal or plan.after
            
            if has_supplements:
                lines.append(f"\n{plan.display_name}")
                
                if plan.before:
                    lines.append("  _За 30 хв до їжі:_")
                    for slot in plan.before:
                        lines.append(f"  • {slot.name}")
                
                if plan.with_meal:
                    lines.append("  _З їжею:_")
                    for slot in plan.with_meal:
                        lines.append(f"  • {slot.name}")
                
                if plan.after:
                    lines.append("  _Через 1-2 год після:_")
                    for slot in plan.after:
                        lines.append(f"  • {slot.name}")
        
        return "\n".join(lines)
    
    def get_meal_supplements(self, plans: Dict[MealTime, MealPlan], 
                             meal: MealTime) -> str:
        """Get formatted supplements for a specific meal"""
        plan = plans[meal]
        lines = [f"{plan.display_name}\n"]
        
        if not (plan.before or plan.with_meal or plan.after):
            lines.append("Немає БАДів для цього прийому їжі")
            return "\n".join(lines)
        
        if plan.before:
            lines.append("⏰ *За 30 хв до їжі:*")
            for slot in plan.before:
                lines.append(f"  • {slot.name}")
                if slot.notes:
                    lines.append(f"    _{slot.notes}_")
        
        if plan.with_meal:
            lines.append("\n🍽 *З їжею:*")
            for slot in plan.with_meal:
                lines.append(f"  • {slot.name}")
                if slot.notes:
                    lines.append(f"    _{slot.notes}_")
        
        if plan.after:
            lines.append("\n⏳ *Через 1-2 год після:*")
            for slot in plan.after:
                lines.append(f"  • {slot.name}")
                if slot.notes:
                    lines.append(f"    _{slot.notes}_")
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test
    import json
    from pathlib import Path
    
    catalog_path = Path(__file__).parent.parent / "data" / "supplement_catalog.json"
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog_data = json.load(f)
    
    constraints = [
        {"type": "separate", "supplements": ["iron", "calcium"], "interval_hours": 2}
    ]
    
    planner = MealPlanner(catalog_data['supplements'], constraints)
    plans = planner.create_plan(["vitamin_d", "omega_3", "iron", "calcium", "magnesium"])
    print(planner.format_plan(plans))

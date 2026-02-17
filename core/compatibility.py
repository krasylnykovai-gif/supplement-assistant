"""
Compatibility Checker: analyzes interactions between selected supplements
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class InteractionType(Enum):
    SYNERGY = "synergy"
    SEPARATE = "separate"
    AVOID = "avoid"

@dataclass
class Interaction:
    supplements: Tuple[str, str]
    type: InteractionType
    interval_hours: int = 0
    reason: str = ""
    source: str = ""

@dataclass 
class CompatibilityReport:
    synergies: List[Interaction]
    separations: List[Interaction]
    warnings: List[Interaction]
    constraints: List[dict]  # For planner

class CompatibilityChecker:
    def __init__(self, interactions_path: str = None):
        if interactions_path is None:
            interactions_path = Path(__file__).parent.parent / "data" / "supplement_interactions.json"
        
        with open(interactions_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.interactions = self._parse_interactions()
    
    def _parse_interactions(self) -> List[Interaction]:
        """Parse JSON interactions into Interaction objects"""
        result = []
        for item in self.data['interactions']:
            pair = tuple(item['pair'])
            interaction = Interaction(
                supplements=pair,
                type=InteractionType(item['type']),
                interval_hours=item.get('interval_hours', 0),
                reason=item.get('reason', ''),
                source=item.get('source', '')
            )
            result.append(interaction)
        return result
    
    def check(self, selected_supplements: List[str]) -> CompatibilityReport:
        """
        Check compatibility between selected supplements.
        Returns a report with synergies, required separations, and warnings.
        """
        synergies = []
        separations = []
        warnings = []
        constraints = []
        
        for interaction in self.interactions:
            supp1, supp2 = interaction.supplements
            
            # Handle "any" wildcard (e.g., psyllium interacts with any supplement)
            if supp2 == "any":
                if supp1 in selected_supplements:
                    for other in selected_supplements:
                        if other != supp1:
                            modified = Interaction(
                                supplements=(supp1, other),
                                type=interaction.type,
                                interval_hours=interaction.interval_hours,
                                reason=interaction.reason,
                                source=interaction.source
                            )
                            if interaction.type == InteractionType.SEPARATE:
                                separations.append(modified)
                                constraints.append({
                                    "type": "separate",
                                    "supplements": [supp1, other],
                                    "interval_hours": interaction.interval_hours
                                })
                continue
            
            # Check if both supplements are in selected list
            if supp1 in selected_supplements and supp2 in selected_supplements:
                if interaction.type == InteractionType.SYNERGY:
                    synergies.append(interaction)
                elif interaction.type == InteractionType.SEPARATE:
                    separations.append(interaction)
                    constraints.append({
                        "type": "separate",
                        "supplements": [supp1, supp2],
                        "interval_hours": interaction.interval_hours
                    })
                elif interaction.type == InteractionType.AVOID:
                    warnings.append(interaction)
                    constraints.append({
                        "type": "avoid",
                        "supplements": [supp1, supp2]
                    })
        
        return CompatibilityReport(
            synergies=synergies,
            separations=separations,
            warnings=warnings,
            constraints=constraints
        )
    
    def format_report(self, report: CompatibilityReport, catalog: dict) -> str:
        """Format compatibility report for Telegram"""
        lines = ["📋 *Звіт сумісності*\n"]
        
        if report.synergies:
            lines.append("✅ *Синергія (підсилюють одне одного):*")
            for s in report.synergies:
                name1 = catalog.get(s.supplements[0], {}).get('name', s.supplements[0])
                name2 = catalog.get(s.supplements[1], {}).get('name', s.supplements[1])
                lines.append(f"• {name1} + {name2}")
                lines.append(f"  _{s.reason}_")
            lines.append("")
        
        if report.separations:
            lines.append("⚠️ *Рознести в часі:*")
            for s in report.separations:
                name1 = catalog.get(s.supplements[0], {}).get('name', s.supplements[0])
                name2 = catalog.get(s.supplements[1], {}).get('name', s.supplements[1])
                lines.append(f"• {name1} ↔ {name2}: мін. {s.interval_hours} год")
                lines.append(f"  _{s.reason}_")
            lines.append("")
        
        if report.warnings:
            lines.append("⛔ *Потребує уваги:*")
            for w in report.warnings:
                name1 = catalog.get(w.supplements[0], {}).get('name', w.supplements[0])
                name2 = catalog.get(w.supplements[1], {}).get('name', w.supplements[1])
                lines.append(f"• {name1} + {name2}")
                lines.append(f"  _{w.reason}_")
            lines.append("")
        
        if not report.synergies and not report.separations and not report.warnings:
            lines.append("✅ Обрані добавки не мають відомих взаємодій між собою.")
        
        return "\n".join(lines)


if __name__ == "__main__":
    checker = CompatibilityChecker()
    report = checker.check(["iron", "calcium", "vitamin_c", "vitamin_d"])
    print("Synergies:", [(s.supplements, s.reason) for s in report.synergies])
    print("Separations:", [(s.supplements, s.interval_hours) for s in report.separations])
    print("Constraints:", report.constraints)

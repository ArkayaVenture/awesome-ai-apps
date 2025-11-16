# Requires: npm i -g @mermaid-js/mermaid-cli
mmdc -i diagrams/architecture.mmd -o images/architecture.png
mmdc -i diagrams/user_journeys.mmd -o images/user_journeys.png
mmdc -i diagrams/use_cases.mmd -o images/use_cases.png
mmdc -i diagrams/gantt.mmd -o images/roadmap.png
Write-Host "Rendered PNGs to images/"
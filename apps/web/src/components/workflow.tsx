import { Icon } from "./icon";

const stages = [
  { title: "Capture the process", description: "Describe the work, its people, and its handoffs.", label: "Source evidence", icon: "file" },
  { title: "Review the details", description: "Check the AI draft against what actually happens.", label: "Human reviewed", icon: "check" },
  { title: "Find opportunities", description: "Compare candidates using evidence and clear criteria.", label: "Evidence-led priority", icon: "layers" },
  { title: "Build the case", description: "Explain recommendations, assumptions, and next steps.", label: "Decision support", icon: "chart" },
] as const;

export function Workflow() {
  return <section className="workflow-section" aria-labelledby="workflow-heading">
    <div className="section-heading"><div><p className="eyebrow">FROM PROCESS TO POSSIBILITY</p><h2 id="workflow-heading">How assessment works</h2></div><span className="quiet-label">The planned assessment journey</span></div>
    <div className="workflow-board"><div className="workflow-track" aria-hidden="true" /><ol className="workflow-stages">{stages.map((stage, index) => <li key={stage.title} className="workflow-stage"><div className="stage-number">0{index + 1}</div><div className="stage-node"><Icon name={stage.icon} size={25} /></div><h3>{stage.title}</h3><p>{stage.description}</p><span className="evidence-chip"><span />{stage.label}</span></li>)}</ol><div className="evidence-rail"><Icon name="shield" size={16} /><span>Evidence stays connected throughout the assessment</span><span className="rail-line" aria-hidden="true" /></div></div>
  </section>;
}

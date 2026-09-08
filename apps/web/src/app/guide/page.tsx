import Link from "next/link";
import { Icon } from "@/components/icon";
import { Workflow } from "@/components/workflow";

export default function Guide() {
  return (
    <div className="page-content">
      <section className="page-intro">
        <p className="eyebrow">ASSESSMENT GUIDE</p>
        <h1>
          Start with the work.
          <br />
          <span>Keep the evidence close.</span>
        </h1>
        <p className="intro-description">
          A useful assessment begins with one process, the people who know it,
          and a clear account of what happens today.
        </p>
      </section>
      <div className="guide-grid">
        <section className="guide-card">
          <span className="guide-icon">
            <Icon name="file" />
          </span>
          <h2>Bring the process into focus</h2>
          <p>
            Choose a workflow with a clear start and finish. Gather what you
            already know:
          </p>
          <ul className="check-list">
            <li>The trigger, steps, handoffs, and expected result</li>
            <li>The people, systems, and documents involved</li>
            <li>Repeated work, exceptions, and common delays</li>
            <li>Available volumes, timings, and their sources</li>
          </ul>
        </section>
        <section className="guide-card" id="evidence">
          <span className="guide-icon">
            <Icon name="shield" />
          </span>
          <h2>Review before you prioritize</h2>
          <p>The assessment keeps human judgment in the loop:</p>
          <ul className="check-list">
            <li>AI extraction produces a draft for human review</li>
            <li>Unknown values stay “Not provided”, never zero</li>
            <li>Confidence is separate from an opportunity score</li>
            <li>ROI estimates explain assumptions and missing inputs</li>
          </ul>
        </section>
      </div>
      <Workflow />
      <section className="guide-next">
        <div>
          <p className="eyebrow">WHAT YOU CAN DO TODAY</p>
          <h2>Start an assessment</h2>
          <p>
            Sign in to create a project, capture a process, review its AI draft,
            and investigate the resulting opportunities.
          </p>
        </div>
        <Link href="/projects" className="button button-secondary">
          Open projects
          <Icon name="arrow" size={17} />
        </Link>
      </section>
    </div>
  );
}

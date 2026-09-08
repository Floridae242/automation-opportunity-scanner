import Link from "next/link";
import { Icon } from "@/components/icon";
import { Workflow } from "@/components/workflow";

export default function Overview() {
  return (
    <div className="page-content">
      <section className="intro">
        <div className="intro-copy">
          <p className="eyebrow">
            <span className="eyebrow-line" />
            PROCESS INTELLIGENCE, WITH CONTEXT
          </p>
          <h1>
            Make the process clear.
            <br />
            <span>Find what comes next.</span>
          </h1>
          <p className="intro-description">
            Understand how work happens before deciding what to automate. Bring
            the evidence, review the details, and build a case you can explain.
          </p>
          <Link className="button button-primary" href="/guide">
            Read the assessment guide
            <Icon name="arrow" size={17} />
          </Link>
        </div>
        <aside className="intro-aside">
          <span className="margin-note">THE STARTING POINT</span>
          <div className="quote-mark" aria-hidden="true">
            “
          </div>
          <p>
            What happens
            <br />
            between the steps?
          </p>
          <span className="aside-rule" />
          <small>
            The handoffs, exceptions, and repeated work are where a useful
            assessment begins.
          </small>
        </aside>
      </section>
      <Workflow />
      <div className="overview-bottom">
        <section
          className="assessments-panel"
          aria-labelledby="assessments-heading"
        >
          <div className="section-heading compact">
            <h2 id="assessments-heading">Your assessments</h2>
            <span className="outline-tag">Workspace</span>
          </div>
          <div className="empty-state">
            <span className="empty-icon">
              <Icon name="folder" size={30} />
            </span>
            <div>
              <h3>Start with a process</h3>
              <p>
                Create a project, add a process, and capture the evidence your
                team can review before prioritizing automation.
              </p>
              <Link href="/projects" className="text-link">
                Open projects
                <Icon name="arrow" size={16} />
              </Link>
            </div>
          </div>
        </section>
        <aside className="principle-card">
          <div className="principle-heading">
            <Icon name="shield" />
            <span>OUR WORKING PRINCIPLE</span>
          </div>
          <h2>
            Confidence comes
            <br />
            from evidence.
          </h2>
          <p>
            Missing information stays visible. AI drafts need human review.
            Every recommendation needs a reason.
          </p>
          <Link className="text-link" href="/guide#evidence">
            Understand the approach
            <Icon name="arrow" size={16} />
          </Link>
        </aside>
      </div>
    </div>
  );
}

import Link from "next/link";

export default function NotFound() {
  return <div className="page-content page-intro"><p className="eyebrow">PAGE NOT FOUND</p><h1>This page isn’t here.</h1><p className="intro-description">Return to the workspace to explore the available pages.</p><Link href="/" className="button button-primary">Back to overview</Link></div>;
}

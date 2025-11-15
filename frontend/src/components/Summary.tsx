interface Props {
  summary: string;
}

export function Summary({ summary }: Props) {
  if (!summary) return null;

  return (
    <section className="summary">
      <h2>Claude&apos;s Recommendation</h2>
      <p>{summary}</p>
    </section>
  );
}





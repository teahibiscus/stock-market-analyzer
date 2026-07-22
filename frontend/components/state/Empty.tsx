type EmptyProps = {
  message: string;
};

export function Empty({ message }: EmptyProps) {
  return (
    <p role="status" aria-live="polite">
      {message}
    </p>
  );
}

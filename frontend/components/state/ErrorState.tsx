type ErrorStateProps = {
  message: string;
};

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <p role="alert" aria-live="assertive">
      {message}
    </p>
  );
}

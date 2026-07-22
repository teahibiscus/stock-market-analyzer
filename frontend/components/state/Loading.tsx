type LoadingProps = {
  message: string;
};

export function Loading({ message }: LoadingProps) {
  return (
    <p role="status" aria-live="polite">
      {message}
    </p>
  );
}

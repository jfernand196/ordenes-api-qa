import type { Estado } from '../api/tipos';

interface Props {
  estado: Estado;
  grande?: boolean;
  testId?: string;
}

export function EstadoBadge({ estado, grande = false, testId }: Props) {
  const clases = `estado estado-${estado.toLowerCase()}${grande ? ' estado-grande' : ''}`;
  return (
    <span className={clases} data-testid={testId}>
      {estado}
    </span>
  );
}

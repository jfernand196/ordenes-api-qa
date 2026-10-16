import { useId } from 'react';

interface CampoProps {
  etiqueta: string;
  valor: string;
  onCambio: (valor: string) => void;
  error?: string;
  numerico?: boolean;
  testId?: string;
}

/** Input con label visible y error accesible (aria-invalid + aria-describedby). */
export function Campo({ etiqueta, valor, onCambio, error, numerico = false, testId }: CampoProps) {
  const id = useId();
  const idError = `${id}-error`;
  return (
    <label htmlFor={id}>
      {etiqueta}
      <input
        id={id}
        value={valor}
        onChange={(e) => onCambio(e.target.value)}
        inputMode={numerico ? 'numeric' : undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? idError : undefined}
        data-testid={testId}
      />
      {error && (
        <span id={idError} className="campo-error">
          {error}
        </span>
      )}
    </label>
  );
}

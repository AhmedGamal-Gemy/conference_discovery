import { useState } from 'react';
import { usePipeline } from '../hooks/usePipeline';
import PipelineStepper from '../components/PipelineStepper';
import ConferenceCard from '../components/ConferenceCard';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const [urlError, setUrlError] = useState('');
  const { steps, conference, isRunning, error, startPipeline, cancelPipeline } = usePipeline();

  const handleRun = () => {
    if (!url.trim()) return;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      setUrlError('Please enter a valid URL starting with http:// or https://');
      return;
    }
    setUrlError('');
    startPipeline(url.trim());
  };

  const handleCancel = () => {
    cancelPipeline();
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    if (urlError) setUrlError('');
  };

  const showStepper = isRunning || steps.length > 0;
  const showResult = conference !== null || (steps.length > 0 && !isRunning && !error);
  const showError = error && !isRunning;

  return (
    <div data-testid="home-page" className="home-page">
      {/* URL Input Section */}
      <div className="url-input-section">
        <h2 className="text-lg font-semibold mb-2">Conference URL</h2>
        <div className="url-input-row">
          <input
            type="url"
            value={url}
            onChange={handleUrlChange}
            placeholder="https://example-conference.org/"
            disabled={isRunning}
            data-testid="url-input"
            className="url-input"
          />
          {isRunning ? (
            <button onClick={handleCancel} data-testid="cancel-button" className="btn-cancel">
              Cancel
            </button>
          ) : (
            <button
              onClick={handleRun}
              disabled={!url.trim()}
              data-testid="run-button"
              className="btn-run"
            >
              Run Pipeline
            </button>
          )}
        </div>
        {urlError && (
          <p className="url-validation-error" data-testid="url-validation-error">
            {urlError}
          </p>
        )}
      </div>

      {/* Stepper */}
      {showStepper && (
        <div className="stepper-section">
          <PipelineStepper steps={steps} />
        </div>
      )}

      {/* Error State */}
      {showError && (
        <div className="error-section" data-testid="pipeline-error">
          <p className="error-message">{error}</p>
          <p className="error-hint">Try a different URL or check that services are running.</p>
        </div>
      )}

      {/* Conference Result */}
      {showResult && (
        <div className="result-section">
          <ConferenceCard conference={conference} isLoading={false} />
        </div>
      )}
    </div>
  );
}

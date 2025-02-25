import React, { useState, useEffect } from 'react';

const ConnectionSelector = ({ onSelect, onCreateNew, onCancel, onEdit, onDelete }) => {
  const [savedConfigs, setSavedConfigs] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState('');

  useEffect(() => {
    const configs = JSON.parse(localStorage.getItem('saved-configs') || '[]');
    setSavedConfigs(configs);
  }, []);

  const handleSelect = () => {
    const config = savedConfigs.find(config => config.name === selectedConfig);
    if (config) {
      onSelect(config, true);
    }
  };

  const handleEdit = () => {
    const config = savedConfigs.find(config => config.name === selectedConfig);
    if (config) {
      onEdit(config);
    }
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this connection?')) {
      onDelete(selectedConfig);
    }
  };

  return (
    <div className="connection-selector">
      <h2>Select a Connection</h2>
      <label htmlFor="connection-select">Saved Connections:</label>
      <select
        id="connection-select"
        value={selectedConfig}
        onChange={(e) => setSelectedConfig(e.target.value)}
      >
        <option value="">Select a connection</option>
        {savedConfigs.map((config, index) => (
          <option key={index} value={config.name}>
            {config.name}
          </option>
        ))}
      </select>
      <div className="button-group">
        <button onClick={handleSelect} disabled={!selectedConfig}>Connect</button>
        <button onClick={handleEdit} disabled={!selectedConfig}>Edit</button>
        <button onClick={handleDelete} disabled={!selectedConfig}>Delete</button>
      </div>
      <div className="button-group secondary">
        <button onClick={onCreateNew}>Create New</button>
        <button onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
};

export default ConnectionSelector;

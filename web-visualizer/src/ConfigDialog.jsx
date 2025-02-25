/* eslint-disable react/prop-types */
const InputField = ({ label, value, onChange, type="text", required=false }) => {
  return (
    <div>
      <label>{label}{required && <span style={{color: 'red'}}>*</span>}</label>
      <input type={type} value={value} onChange={onChange} required={required} />
    </div>
  );
};

const ConfigDialog = ({ open, config, setConfig, onClose, isNewConfig, savedConfigs }) => {
  if (!open) {
    return null;
  }

  const handleConnectionTypeChange = (e) => {
    const newType = e.target.value;
    setConfig(prevConfig => ({
      ...prevConfig,
      connectionType: newType,
    }));
  };

  return (
    <div className="config-dialog">
      <div className="config-dialog-content">
        <InputField
          label="Configuration Name"
          value={config.name || ''}
          onChange={(e) => setConfig(prevConfig => ({...prevConfig, name: e.target.value}))}
          required={true}
        />
        <div>
          <label>Connection Type</label>
          <select 
            value={config.connectionType || 'solace'} 
            onChange={handleConnectionTypeChange}
          >
            <option value="solace">Solace Broker</option>
            <option value="websocket">WebSocket</option>
          </select>
        </div>
        {(config.connectionType || 'solace') === 'solace' ? (
          <>
            <InputField
              label="Solace URL"
              value={config.url || ''}
              onChange={(e) => setConfig(prevConfig => ({...prevConfig, url: e.target.value}))}
            />
            <InputField
              label="VPN Name"
              value={config.vpnName || ''}
              onChange={(e) => setConfig(prevConfig => ({...prevConfig, vpnName: e.target.value}))}
            />
            <InputField
              label="Username"
              value={config.userName || ''}
              onChange={(e) => setConfig(prevConfig => ({...prevConfig, userName: e.target.value}))}
            />
            <InputField
              label="Password"
              value={config.password || ''}
              type="password"
              onChange={(e) => setConfig(prevConfig => ({...prevConfig, password: e.target.value}))}
            />
            <InputField
              label="Namespace"
              value={config.namespace || ''}
              onChange={(e) => setConfig(prevConfig => ({...prevConfig, namespace: e.target.value}))}
            />
          </>
        ) : (
          <InputField
            label="WebSocket URL"
            value={config.websocketUrl || ''}
            onChange={(e) => setConfig(prevConfig => ({...prevConfig, websocketUrl: e.target.value}))}
          />
        )}
      </div>
      <div className="config-dialog-buttons">
        <button className="button" onClick={() => onClose(false)}>Cancel</button>
        <button 
          className="button button-info" 
          onClick={() => {
            if (!config.name) {
              alert('Configuration Name is required');
              return;
            }
            if (isNewConfig && savedConfigs.some(c => c.name === config.name)) {
              alert('Configuration Name must be unique');
              return;
            }
            onClose(true);
          }}
        >
          {isNewConfig ? 'Save and Connect' : 'Connect'}
        </button>
      </div>
    </div>
  );
};

export default ConfigDialog;

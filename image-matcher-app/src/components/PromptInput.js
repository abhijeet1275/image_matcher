import React from 'react';

function PromptInput({ prompt, onPromptChange }) {
    const handleInputChange = (event) => {
        onPromptChange(event.target.value);
    };

    return (
        <div className="prompt-container">
            <input
                type="text"
                value={prompt}
                onChange={handleInputChange}
                placeholder="Enter a prompt..."
            />
        </div>
    );
}

export default PromptInput;
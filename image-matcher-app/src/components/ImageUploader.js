import React from 'react';

function ImageUploader({ onImagesChange }) {
    const handleFileChange = (event) => {
        if (event.target.files && event.target.files.length > 0) {
            // Pass the FileList object up to the parent
            onImagesChange(Array.from(event.target.files));
        }
    };

    return (
        <div className="uploader-container">
            <input
                type="file"
                onChange={handleFileChange}
                accept="image/*"
                multiple
            />
        </div>
    );
}

export default ImageUploader;
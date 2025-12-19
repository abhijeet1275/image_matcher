# Image Matcher App

This project is a React application that allows users to upload images and enter a prompt to match the images against the prompt. The application calculates and displays the similarity percentage between the uploaded images and the provided prompt.

## Features

- Upload images using a user-friendly interface.
- Input a prompt to match against the uploaded images.
- Display the similarity percentage for each image based on the prompt.

## Technologies Used

- React
- OpenCLIP for image and text matching
- CSS for styling

## Project Structure

```
image-matcher-app
├── public
│   └── index.html          # Main HTML file
├── src
│   ├── components
│   │   ├── ImageUploader.js # Component for uploading images
│   │   └── PromptInput.js   # Component for entering prompts
│   ├── App.css             # CSS styles for the application
│   ├── App.js              # Main application component
│   └── index.js            # Entry point of the React application
├── package.json            # npm configuration file
└── README.md               # Project documentation
```

## Getting Started

To get started with the Image Matcher App, follow these steps:

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd image-matcher-app
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Run the application:**
   ```
   npm start
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000` to view the application.

## Usage

1. Upload an image using the upload button.
2. Enter a prompt in the input field.
3. Click the "Match" button to see the similarity percentage for the uploaded image against the prompt.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
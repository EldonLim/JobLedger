const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
    entry: {
        popup: './src/popup.js',
        content: './src/content.js'
    },
    output: {
        filename: '[name].js',
        path: path.resolve(__dirname, 'dist')
    },
    mode: 'development',
    watch: true,
    plugins: [
        new CopyWebpackPlugin({
            patterns: [{from: 'static'}]
        })
    ],

}
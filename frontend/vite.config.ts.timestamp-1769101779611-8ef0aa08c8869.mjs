// vite.config.ts
import path from "path";
import { fileURLToPath } from "url";
import { defineConfig } from "file:///C:/Users/hp/Downloads/New%20folder/New%20folder/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/hp/Downloads/New%20folder/New%20folder/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
import tailwindcss from "file:///C:/Users/hp/Downloads/New%20folder/New%20folder/frontend/node_modules/@tailwindcss/vite/dist/index.mjs";
var __vite_injected_original_import_meta_url = "file:///C:/Users/hp/Downloads/New%20folder/New%20folder/frontend/vite.config.ts";
var __filepath = fileURLToPath(__vite_injected_original_import_meta_url);
var __dirname = path.dirname(__filepath);
console.log("Vite Config - __dirname:", __dirname);
console.log("Vite Config - cwd:", process.cwd());
var vite_config_default = defineConfig({
  root: __dirname,
  plugins: [
    react({
      // Enable Fast Refresh
      fastRefresh: true
    }),
    tailwindcss()
  ],
  build: {
    // Target modern browsers for smaller bundles
    target: "es2020",
    rollupOptions: {
      input: path.resolve(__dirname, "index.html"),
      output: {
        // Optimized code splitting
        manualChunks: {
          // Core React libraries
          "react-vendor": ["react", "react-dom"],
          // Router separate for better caching
          "router": ["react-router-dom"],
          // Video players (large dependencies)
          "video-vendor": ["hls.js"],
          // Icons (can be large)
          "icons": ["lucide-react"]
        },
        // Optimize chunk names for better caching
        chunkFileNames: "assets/[name]-[hash].js",
        entryFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]"
      }
    },
    // Increase chunk size warning limit
    chunkSizeWarningLimit: 1e3,
    // Use esbuild for faster minification
    minify: "esbuild",
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Source maps only for errors (smaller build)
    sourcemap: false,
    // Optimize dependencies
    commonjsOptions: {
      transformMixedEsModules: true
    }
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    },
    extensions: [".mjs", ".js", ".mts", ".ts", ".jsx", ".tsx", ".json"]
  },
  server: {
    port: 3e3,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  // Optimize dependencies
  optimizeDeps: {
    include: [
      "react",
      "react-dom",
      "react-router-dom",
      "hls.js",
      "lucide-react"
    ],
    // Exclude large dependencies that don't need pre-bundling
    exclude: ["video.js", "@videojs/http-streaming"]
  },
  // Performance optimizations
  esbuild: {
    // Remove debugger statements in production
    drop: import.meta.env?.MODE === "production" ? ["debugger", "console"] : [],
    // Optimize for speed
    legalComments: "none"
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxocFxcXFxEb3dubG9hZHNcXFxcTmV3IGZvbGRlclxcXFxOZXcgZm9sZGVyXFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxocFxcXFxEb3dubG9hZHNcXFxcTmV3IGZvbGRlclxcXFxOZXcgZm9sZGVyXFxcXGZyb250ZW5kXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9Vc2Vycy9ocC9Eb3dubG9hZHMvTmV3JTIwZm9sZGVyL05ldyUyMGZvbGRlci9mcm9udGVuZC92aXRlLmNvbmZpZy50c1wiO2ltcG9ydCBwYXRoIGZyb20gXCJwYXRoXCJcclxuaW1wb3J0IHsgZmlsZVVSTFRvUGF0aCB9IGZyb20gXCJ1cmxcIlxyXG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xyXG5pbXBvcnQgcmVhY3QgZnJvbSAnQHZpdGVqcy9wbHVnaW4tcmVhY3QnXHJcbmltcG9ydCB0YWlsd2luZGNzcyBmcm9tICdAdGFpbHdpbmRjc3Mvdml0ZSdcclxuXHJcbmNvbnN0IF9fZmlsZXBhdGggPSBmaWxlVVJMVG9QYXRoKGltcG9ydC5tZXRhLnVybCk7XHJcbmNvbnN0IF9fZGlybmFtZSA9IHBhdGguZGlybmFtZShfX2ZpbGVwYXRoKTtcclxuXHJcbmNvbnNvbGUubG9nKFwiVml0ZSBDb25maWcgLSBfX2Rpcm5hbWU6XCIsIF9fZGlybmFtZSk7XHJcbmNvbnNvbGUubG9nKFwiVml0ZSBDb25maWcgLSBjd2Q6XCIsIHByb2Nlc3MuY3dkKCkpO1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICByb290OiBfX2Rpcm5hbWUsXHJcbiAgcGx1Z2luczogW1xyXG4gICAgcmVhY3Qoe1xyXG4gICAgICAvLyBFbmFibGUgRmFzdCBSZWZyZXNoXHJcbiAgICAgIGZhc3RSZWZyZXNoOiB0cnVlLFxyXG4gICAgfSksIFxyXG4gICAgdGFpbHdpbmRjc3MoKVxyXG4gIF0sXHJcbiAgYnVpbGQ6IHtcclxuICAgIC8vIFRhcmdldCBtb2Rlcm4gYnJvd3NlcnMgZm9yIHNtYWxsZXIgYnVuZGxlc1xyXG4gICAgdGFyZ2V0OiAnZXMyMDIwJyxcclxuICAgIHJvbGx1cE9wdGlvbnM6IHtcclxuICAgICAgaW5wdXQ6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsICdpbmRleC5odG1sJyksXHJcbiAgICAgIG91dHB1dDoge1xyXG4gICAgICAgIC8vIE9wdGltaXplZCBjb2RlIHNwbGl0dGluZ1xyXG4gICAgICAgIG1hbnVhbENodW5rczoge1xyXG4gICAgICAgICAgLy8gQ29yZSBSZWFjdCBsaWJyYXJpZXNcclxuICAgICAgICAgICdyZWFjdC12ZW5kb3InOiBbJ3JlYWN0JywgJ3JlYWN0LWRvbSddLFxyXG4gICAgICAgICAgLy8gUm91dGVyIHNlcGFyYXRlIGZvciBiZXR0ZXIgY2FjaGluZ1xyXG4gICAgICAgICAgJ3JvdXRlcic6IFsncmVhY3Qtcm91dGVyLWRvbSddLFxyXG4gICAgICAgICAgLy8gVmlkZW8gcGxheWVycyAobGFyZ2UgZGVwZW5kZW5jaWVzKVxyXG4gICAgICAgICAgJ3ZpZGVvLXZlbmRvcic6IFsnaGxzLmpzJ10sXHJcbiAgICAgICAgICAvLyBJY29ucyAoY2FuIGJlIGxhcmdlKVxyXG4gICAgICAgICAgJ2ljb25zJzogWydsdWNpZGUtcmVhY3QnXSxcclxuICAgICAgICB9LFxyXG4gICAgICAgIC8vIE9wdGltaXplIGNodW5rIG5hbWVzIGZvciBiZXR0ZXIgY2FjaGluZ1xyXG4gICAgICAgIGNodW5rRmlsZU5hbWVzOiAnYXNzZXRzL1tuYW1lXS1baGFzaF0uanMnLFxyXG4gICAgICAgIGVudHJ5RmlsZU5hbWVzOiAnYXNzZXRzL1tuYW1lXS1baGFzaF0uanMnLFxyXG4gICAgICAgIGFzc2V0RmlsZU5hbWVzOiAnYXNzZXRzL1tuYW1lXS1baGFzaF0uW2V4dF0nLFxyXG4gICAgICB9LFxyXG4gICAgfSxcclxuICAgIC8vIEluY3JlYXNlIGNodW5rIHNpemUgd2FybmluZyBsaW1pdFxyXG4gICAgY2h1bmtTaXplV2FybmluZ0xpbWl0OiAxMDAwLFxyXG4gICAgLy8gVXNlIGVzYnVpbGQgZm9yIGZhc3RlciBtaW5pZmljYXRpb25cclxuICAgIG1pbmlmeTogJ2VzYnVpbGQnLFxyXG4gICAgLy8gRW5hYmxlIENTUyBjb2RlIHNwbGl0dGluZ1xyXG4gICAgY3NzQ29kZVNwbGl0OiB0cnVlLFxyXG4gICAgLy8gU291cmNlIG1hcHMgb25seSBmb3IgZXJyb3JzIChzbWFsbGVyIGJ1aWxkKVxyXG4gICAgc291cmNlbWFwOiBmYWxzZSxcclxuICAgIC8vIE9wdGltaXplIGRlcGVuZGVuY2llc1xyXG4gICAgY29tbW9uanNPcHRpb25zOiB7XHJcbiAgICAgIHRyYW5zZm9ybU1peGVkRXNNb2R1bGVzOiB0cnVlLFxyXG4gICAgfSxcclxuICB9LFxyXG4gIHJlc29sdmU6IHtcclxuICAgIGFsaWFzOiB7XHJcbiAgICAgIFwiQFwiOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcIi4vc3JjXCIpLFxyXG4gICAgfSxcclxuICAgIGV4dGVuc2lvbnM6IFsnLm1qcycsICcuanMnLCAnLm10cycsICcudHMnLCAnLmpzeCcsICcudHN4JywgJy5qc29uJ11cclxuICB9LFxyXG4gIHNlcnZlcjoge1xyXG4gICAgcG9ydDogMzAwMCxcclxuICAgIHByb3h5OiB7XHJcbiAgICAgICcvYXBpJzoge1xyXG4gICAgICAgIHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODAwMCcsXHJcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxyXG4gICAgICB9LFxyXG4gICAgfSxcclxuICB9LFxyXG4gIC8vIE9wdGltaXplIGRlcGVuZGVuY2llc1xyXG4gIG9wdGltaXplRGVwczoge1xyXG4gICAgaW5jbHVkZTogW1xyXG4gICAgICAncmVhY3QnLFxyXG4gICAgICAncmVhY3QtZG9tJyxcclxuICAgICAgJ3JlYWN0LXJvdXRlci1kb20nLFxyXG4gICAgICAnaGxzLmpzJyxcclxuICAgICAgJ2x1Y2lkZS1yZWFjdCdcclxuICAgIF0sXHJcbiAgICAvLyBFeGNsdWRlIGxhcmdlIGRlcGVuZGVuY2llcyB0aGF0IGRvbid0IG5lZWQgcHJlLWJ1bmRsaW5nXHJcbiAgICBleGNsdWRlOiBbJ3ZpZGVvLmpzJywgJ0B2aWRlb2pzL2h0dHAtc3RyZWFtaW5nJ10sXHJcbiAgfSxcclxuICAvLyBQZXJmb3JtYW5jZSBvcHRpbWl6YXRpb25zXHJcbiAgZXNidWlsZDoge1xyXG4gICAgLy8gUmVtb3ZlIGRlYnVnZ2VyIHN0YXRlbWVudHMgaW4gcHJvZHVjdGlvblxyXG4gICAgZHJvcDogaW1wb3J0Lm1ldGEuZW52Py5NT0RFID09PSAncHJvZHVjdGlvbicgPyBbJ2RlYnVnZ2VyJywgJ2NvbnNvbGUnXSA6IFtdLFxyXG4gICAgLy8gT3B0aW1pemUgZm9yIHNwZWVkXHJcbiAgICBsZWdhbENvbW1lbnRzOiAnbm9uZScsXHJcbiAgfSxcclxufSlcclxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUFnVyxPQUFPLFVBQVU7QUFDalgsU0FBUyxxQkFBcUI7QUFDOUIsU0FBUyxvQkFBb0I7QUFDN0IsT0FBTyxXQUFXO0FBQ2xCLE9BQU8saUJBQWlCO0FBSnFNLElBQU0sMkNBQTJDO0FBTTlRLElBQU0sYUFBYSxjQUFjLHdDQUFlO0FBQ2hELElBQU0sWUFBWSxLQUFLLFFBQVEsVUFBVTtBQUV6QyxRQUFRLElBQUksNEJBQTRCLFNBQVM7QUFDakQsUUFBUSxJQUFJLHNCQUFzQixRQUFRLElBQUksQ0FBQztBQUUvQyxJQUFPLHNCQUFRLGFBQWE7QUFBQSxFQUMxQixNQUFNO0FBQUEsRUFDTixTQUFTO0FBQUEsSUFDUCxNQUFNO0FBQUE7QUFBQSxNQUVKLGFBQWE7QUFBQSxJQUNmLENBQUM7QUFBQSxJQUNELFlBQVk7QUFBQSxFQUNkO0FBQUEsRUFDQSxPQUFPO0FBQUE7QUFBQSxJQUVMLFFBQVE7QUFBQSxJQUNSLGVBQWU7QUFBQSxNQUNiLE9BQU8sS0FBSyxRQUFRLFdBQVcsWUFBWTtBQUFBLE1BQzNDLFFBQVE7QUFBQTtBQUFBLFFBRU4sY0FBYztBQUFBO0FBQUEsVUFFWixnQkFBZ0IsQ0FBQyxTQUFTLFdBQVc7QUFBQTtBQUFBLFVBRXJDLFVBQVUsQ0FBQyxrQkFBa0I7QUFBQTtBQUFBLFVBRTdCLGdCQUFnQixDQUFDLFFBQVE7QUFBQTtBQUFBLFVBRXpCLFNBQVMsQ0FBQyxjQUFjO0FBQUEsUUFDMUI7QUFBQTtBQUFBLFFBRUEsZ0JBQWdCO0FBQUEsUUFDaEIsZ0JBQWdCO0FBQUEsUUFDaEIsZ0JBQWdCO0FBQUEsTUFDbEI7QUFBQSxJQUNGO0FBQUE7QUFBQSxJQUVBLHVCQUF1QjtBQUFBO0FBQUEsSUFFdkIsUUFBUTtBQUFBO0FBQUEsSUFFUixjQUFjO0FBQUE7QUFBQSxJQUVkLFdBQVc7QUFBQTtBQUFBLElBRVgsaUJBQWlCO0FBQUEsTUFDZix5QkFBeUI7QUFBQSxJQUMzQjtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssS0FBSyxRQUFRLFdBQVcsT0FBTztBQUFBLElBQ3RDO0FBQUEsSUFDQSxZQUFZLENBQUMsUUFBUSxPQUFPLFFBQVEsT0FBTyxRQUFRLFFBQVEsT0FBTztBQUFBLEVBQ3BFO0FBQUEsRUFDQSxRQUFRO0FBQUEsSUFDTixNQUFNO0FBQUEsSUFDTixPQUFPO0FBQUEsTUFDTCxRQUFRO0FBQUEsUUFDTixRQUFRO0FBQUEsUUFDUixjQUFjO0FBQUEsTUFDaEI7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBO0FBQUEsRUFFQSxjQUFjO0FBQUEsSUFDWixTQUFTO0FBQUEsTUFDUDtBQUFBLE1BQ0E7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxJQUNGO0FBQUE7QUFBQSxJQUVBLFNBQVMsQ0FBQyxZQUFZLHlCQUF5QjtBQUFBLEVBQ2pEO0FBQUE7QUFBQSxFQUVBLFNBQVM7QUFBQTtBQUFBLElBRVAsTUFBTSxZQUFZLEtBQUssU0FBUyxlQUFlLENBQUMsWUFBWSxTQUFTLElBQUksQ0FBQztBQUFBO0FBQUEsSUFFMUUsZUFBZTtBQUFBLEVBQ2pCO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K

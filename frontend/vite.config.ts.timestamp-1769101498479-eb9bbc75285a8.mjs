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
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxocFxcXFxEb3dubG9hZHNcXFxcTmV3IGZvbGRlclxcXFxOZXcgZm9sZGVyXFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxocFxcXFxEb3dubG9hZHNcXFxcTmV3IGZvbGRlclxcXFxOZXcgZm9sZGVyXFxcXGZyb250ZW5kXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9Vc2Vycy9ocC9Eb3dubG9hZHMvTmV3JTIwZm9sZGVyL05ldyUyMGZvbGRlci9mcm9udGVuZC92aXRlLmNvbmZpZy50c1wiO2ltcG9ydCBwYXRoIGZyb20gXCJwYXRoXCJcclxuaW1wb3J0IHsgZmlsZVVSTFRvUGF0aCB9IGZyb20gXCJ1cmxcIlxyXG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xyXG5pbXBvcnQgcmVhY3QgZnJvbSAnQHZpdGVqcy9wbHVnaW4tcmVhY3QnXHJcbmltcG9ydCB0YWlsd2luZGNzcyBmcm9tICdAdGFpbHdpbmRjc3Mvdml0ZSdcclxuXHJcbmNvbnN0IF9fZmlsZXBhdGggPSBmaWxlVVJMVG9QYXRoKGltcG9ydC5tZXRhLnVybCk7XHJcbmNvbnN0IF9fZGlybmFtZSA9IHBhdGguZGlybmFtZShfX2ZpbGVwYXRoKTtcclxuXHJcbmNvbnNvbGUubG9nKFwiVml0ZSBDb25maWcgLSBfX2Rpcm5hbWU6XCIsIF9fZGlybmFtZSk7XHJcbmNvbnNvbGUubG9nKFwiVml0ZSBDb25maWcgLSBjd2Q6XCIsIHByb2Nlc3MuY3dkKCkpO1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICByb290OiBfX2Rpcm5hbWUsXHJcbiAgcGx1Z2luczogW1xyXG4gICAgcmVhY3Qoe1xyXG4gICAgICAvLyBFbmFibGUgRmFzdCBSZWZyZXNoXHJcbiAgICAgIGZhc3RSZWZyZXNoOiB0cnVlLFxyXG4gICAgfSksIFxyXG4gICAgdGFpbHdpbmRjc3MoKVxyXG4gIF0sXHJcbiAgYnVpbGQ6IHtcclxuICAgIC8vIFRhcmdldCBtb2Rlcm4gYnJvd3NlcnMgZm9yIHNtYWxsZXIgYnVuZGxlc1xyXG4gICAgdGFyZ2V0OiAnZXMyMDIwJyxcclxuICAgIHJvbGx1cE9wdGlvbnM6IHtcclxuICAgICAgaW5wdXQ6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsICdpbmRleC5odG1sJyksXHJcbiAgICAgIG91dHB1dDoge1xyXG4gICAgICAgIC8vIE9wdGltaXplZCBjb2RlIHNwbGl0dGluZ1xyXG4gICAgICAgIG1hbnVhbENodW5rczoge1xyXG4gICAgICAgICAgLy8gQ29yZSBSZWFjdCBsaWJyYXJpZXNcclxuICAgICAgICAgICdyZWFjdC12ZW5kb3InOiBbJ3JlYWN0JywgJ3JlYWN0LWRvbSddLFxyXG4gICAgICAgICAgLy8gUm91dGVyIHNlcGFyYXRlIGZvciBiZXR0ZXIgY2FjaGluZ1xyXG4gICAgICAgICAgJ3JvdXRlcic6IFsncmVhY3Qtcm91dGVyLWRvbSddLFxyXG4gICAgICAgICAgLy8gVmlkZW8gcGxheWVycyAobGFyZ2UgZGVwZW5kZW5jaWVzKVxyXG4gICAgICAgICAgJ3ZpZGVvLXZlbmRvcic6IFsnaGxzLmpzJ10sXHJcbiAgICAgICAgICAvLyBJY29ucyAoY2FuIGJlIGxhcmdlKVxyXG4gICAgICAgICAgJ2ljb25zJzogWydsdWNpZGUtcmVhY3QnXSxcclxuICAgICAgICB9LFxyXG4gICAgICAgIC8vIE9wdGltaXplIGNodW5rIG5hbWVzIGZvciBiZXR0ZXIgY2FjaGluZ1xyXG4gICAgICAgIGNodW5rRmlsZU5hbWVzOiAnYXNzZXRzL1tuYW1lXS1baGFzaF0uanMnLFxyXG4gICAgICAgIGVudHJ5RmlsZU5hbWVzOiAnYXNzZXRzL1tuYW1lXS1baGFzaF0uanMnLFxyXG4gICAgICAgIGFzc2V0RmlsZU5hbWVzOiAnYXNzZXRzL1tuYW1lXS1baGFzaF0uW2V4dF0nLFxyXG4gICAgICB9LFxyXG4gICAgfSxcclxuICAgIC8vIEluY3JlYXNlIGNodW5rIHNpemUgd2FybmluZyBsaW1pdFxyXG4gICAgY2h1bmtTaXplV2FybmluZ0xpbWl0OiAxMDAwLFxyXG4gICAgLy8gVXNlIGVzYnVpbGQgZm9yIGZhc3RlciBtaW5pZmljYXRpb25cclxuICAgIG1pbmlmeTogJ2VzYnVpbGQnLFxyXG4gICAgLy8gRW5hYmxlIENTUyBjb2RlIHNwbGl0dGluZ1xyXG4gICAgY3NzQ29kZVNwbGl0OiB0cnVlLFxyXG4gICAgLy8gU291cmNlIG1hcHMgb25seSBmb3IgZXJyb3JzIChzbWFsbGVyIGJ1aWxkKVxyXG4gICAgc291cmNlbWFwOiBmYWxzZSxcclxuICAgIC8vIE9wdGltaXplIGRlcGVuZGVuY2llc1xyXG4gICAgY29tbW9uanNPcHRpb25zOiB7XHJcbiAgICAgIHRyYW5zZm9ybU1peGVkRXNNb2R1bGVzOiB0cnVlLFxyXG4gICAgfSxcclxuICB9LFxyXG4gIHJlc29sdmU6IHtcclxuICAgIGFsaWFzOiB7XHJcbiAgICAgIFwiQFwiOiBwYXRoLnJlc29sdmUoX19kaXJuYW1lLCBcIi4vc3JjXCIpLFxyXG4gICAgfSxcclxuICAgIGV4dGVuc2lvbnM6IFsnLm1qcycsICcuanMnLCAnLm10cycsICcudHMnLCAnLmpzeCcsICcudHN4JywgJy5qc29uJ11cclxuICB9LFxyXG4gIHNlcnZlcjoge1xyXG4gICAgcHJveHk6IHtcclxuICAgICAgJy9hcGknOiB7XHJcbiAgICAgICAgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDAwJyxcclxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gIH0sXHJcbiAgLy8gT3B0aW1pemUgZGVwZW5kZW5jaWVzXHJcbiAgb3B0aW1pemVEZXBzOiB7XHJcbiAgICBpbmNsdWRlOiBbXHJcbiAgICAgICdyZWFjdCcsXHJcbiAgICAgICdyZWFjdC1kb20nLFxyXG4gICAgICAncmVhY3Qtcm91dGVyLWRvbScsXHJcbiAgICAgICdobHMuanMnLFxyXG4gICAgICAnbHVjaWRlLXJlYWN0J1xyXG4gICAgXSxcclxuICAgIC8vIEV4Y2x1ZGUgbGFyZ2UgZGVwZW5kZW5jaWVzIHRoYXQgZG9uJ3QgbmVlZCBwcmUtYnVuZGxpbmdcclxuICAgIGV4Y2x1ZGU6IFsndmlkZW8uanMnLCAnQHZpZGVvanMvaHR0cC1zdHJlYW1pbmcnXSxcclxuICB9LFxyXG4gIC8vIFBlcmZvcm1hbmNlIG9wdGltaXphdGlvbnNcclxuICBlc2J1aWxkOiB7XHJcbiAgICAvLyBSZW1vdmUgZGVidWdnZXIgc3RhdGVtZW50cyBpbiBwcm9kdWN0aW9uXHJcbiAgICBkcm9wOiBpbXBvcnQubWV0YS5lbnY/Lk1PREUgPT09ICdwcm9kdWN0aW9uJyA/IFsnZGVidWdnZXInLCAnY29uc29sZSddIDogW10sXHJcbiAgICAvLyBPcHRpbWl6ZSBmb3Igc3BlZWRcclxuICAgIGxlZ2FsQ29tbWVudHM6ICdub25lJyxcclxuICB9LFxyXG59KVxyXG4iXSwKICAibWFwcGluZ3MiOiAiO0FBQWdXLE9BQU8sVUFBVTtBQUNqWCxTQUFTLHFCQUFxQjtBQUM5QixTQUFTLG9CQUFvQjtBQUM3QixPQUFPLFdBQVc7QUFDbEIsT0FBTyxpQkFBaUI7QUFKcU0sSUFBTSwyQ0FBMkM7QUFNOVEsSUFBTSxhQUFhLGNBQWMsd0NBQWU7QUFDaEQsSUFBTSxZQUFZLEtBQUssUUFBUSxVQUFVO0FBRXpDLFFBQVEsSUFBSSw0QkFBNEIsU0FBUztBQUNqRCxRQUFRLElBQUksc0JBQXNCLFFBQVEsSUFBSSxDQUFDO0FBRS9DLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLE1BQU07QUFBQSxFQUNOLFNBQVM7QUFBQSxJQUNQLE1BQU07QUFBQTtBQUFBLE1BRUosYUFBYTtBQUFBLElBQ2YsQ0FBQztBQUFBLElBQ0QsWUFBWTtBQUFBLEVBQ2Q7QUFBQSxFQUNBLE9BQU87QUFBQTtBQUFBLElBRUwsUUFBUTtBQUFBLElBQ1IsZUFBZTtBQUFBLE1BQ2IsT0FBTyxLQUFLLFFBQVEsV0FBVyxZQUFZO0FBQUEsTUFDM0MsUUFBUTtBQUFBO0FBQUEsUUFFTixjQUFjO0FBQUE7QUFBQSxVQUVaLGdCQUFnQixDQUFDLFNBQVMsV0FBVztBQUFBO0FBQUEsVUFFckMsVUFBVSxDQUFDLGtCQUFrQjtBQUFBO0FBQUEsVUFFN0IsZ0JBQWdCLENBQUMsUUFBUTtBQUFBO0FBQUEsVUFFekIsU0FBUyxDQUFDLGNBQWM7QUFBQSxRQUMxQjtBQUFBO0FBQUEsUUFFQSxnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxNQUNsQjtBQUFBLElBQ0Y7QUFBQTtBQUFBLElBRUEsdUJBQXVCO0FBQUE7QUFBQSxJQUV2QixRQUFRO0FBQUE7QUFBQSxJQUVSLGNBQWM7QUFBQTtBQUFBLElBRWQsV0FBVztBQUFBO0FBQUEsSUFFWCxpQkFBaUI7QUFBQSxNQUNmLHlCQUF5QjtBQUFBLElBQzNCO0FBQUEsRUFDRjtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxLQUFLLFFBQVEsV0FBVyxPQUFPO0FBQUEsSUFDdEM7QUFBQSxJQUNBLFlBQVksQ0FBQyxRQUFRLE9BQU8sUUFBUSxPQUFPLFFBQVEsUUFBUSxPQUFPO0FBQUEsRUFDcEU7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQUE7QUFBQSxFQUVBLGNBQWM7QUFBQSxJQUNaLFNBQVM7QUFBQSxNQUNQO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLElBQ0Y7QUFBQTtBQUFBLElBRUEsU0FBUyxDQUFDLFlBQVkseUJBQXlCO0FBQUEsRUFDakQ7QUFBQTtBQUFBLEVBRUEsU0FBUztBQUFBO0FBQUEsSUFFUCxNQUFNLFlBQVksS0FBSyxTQUFTLGVBQWUsQ0FBQyxZQUFZLFNBQVMsSUFBSSxDQUFDO0FBQUE7QUFBQSxJQUUxRSxlQUFlO0FBQUEsRUFDakI7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=

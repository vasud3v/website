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
    react(),
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
    port: 5174,
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
    drop: process.env.NODE_ENV === "production" ? ["debugger", "console"] : [],
    // Optimize for speed
    legalComments: "none"
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxocFxcXFxEb3dubG9hZHNcXFxcTmV3IGZvbGRlclxcXFxOZXcgZm9sZGVyXFxcXGZyb250ZW5kXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ZpbGVuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxocFxcXFxEb3dubG9hZHNcXFxcTmV3IGZvbGRlclxcXFxOZXcgZm9sZGVyXFxcXGZyb250ZW5kXFxcXHZpdGUuY29uZmlnLnRzXCI7Y29uc3QgX192aXRlX2luamVjdGVkX29yaWdpbmFsX2ltcG9ydF9tZXRhX3VybCA9IFwiZmlsZTovLy9DOi9Vc2Vycy9ocC9Eb3dubG9hZHMvTmV3JTIwZm9sZGVyL05ldyUyMGZvbGRlci9mcm9udGVuZC92aXRlLmNvbmZpZy50c1wiO2ltcG9ydCBwYXRoIGZyb20gXCJwYXRoXCJcclxuaW1wb3J0IHsgZmlsZVVSTFRvUGF0aCB9IGZyb20gXCJ1cmxcIlxyXG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xyXG5pbXBvcnQgcmVhY3QgZnJvbSAnQHZpdGVqcy9wbHVnaW4tcmVhY3QnXHJcbmltcG9ydCB0YWlsd2luZGNzcyBmcm9tICdAdGFpbHdpbmRjc3Mvdml0ZSdcclxuXHJcbmNvbnN0IF9fZmlsZXBhdGggPSBmaWxlVVJMVG9QYXRoKGltcG9ydC5tZXRhLnVybCk7XHJcbmNvbnN0IF9fZGlybmFtZSA9IHBhdGguZGlybmFtZShfX2ZpbGVwYXRoKTtcclxuXHJcbmNvbnNvbGUubG9nKFwiVml0ZSBDb25maWcgLSBfX2Rpcm5hbWU6XCIsIF9fZGlybmFtZSk7XHJcbmNvbnNvbGUubG9nKFwiVml0ZSBDb25maWcgLSBjd2Q6XCIsIHByb2Nlc3MuY3dkKCkpO1xyXG5cclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICByb290OiBfX2Rpcm5hbWUsXHJcbiAgcGx1Z2luczogW1xyXG4gICAgcmVhY3QoKSwgXHJcbiAgICB0YWlsd2luZGNzcygpXHJcbiAgXSxcclxuICBidWlsZDoge1xyXG4gICAgLy8gVGFyZ2V0IG1vZGVybiBicm93c2VycyBmb3Igc21hbGxlciBidW5kbGVzXHJcbiAgICB0YXJnZXQ6ICdlczIwMjAnLFxyXG4gICAgcm9sbHVwT3B0aW9uczoge1xyXG4gICAgICBpbnB1dDogcGF0aC5yZXNvbHZlKF9fZGlybmFtZSwgJ2luZGV4Lmh0bWwnKSxcclxuICAgICAgb3V0cHV0OiB7XHJcbiAgICAgICAgLy8gT3B0aW1pemVkIGNvZGUgc3BsaXR0aW5nXHJcbiAgICAgICAgbWFudWFsQ2h1bmtzOiB7XHJcbiAgICAgICAgICAvLyBDb3JlIFJlYWN0IGxpYnJhcmllc1xyXG4gICAgICAgICAgJ3JlYWN0LXZlbmRvcic6IFsncmVhY3QnLCAncmVhY3QtZG9tJ10sXHJcbiAgICAgICAgICAvLyBSb3V0ZXIgc2VwYXJhdGUgZm9yIGJldHRlciBjYWNoaW5nXHJcbiAgICAgICAgICAncm91dGVyJzogWydyZWFjdC1yb3V0ZXItZG9tJ10sXHJcbiAgICAgICAgICAvLyBWaWRlbyBwbGF5ZXJzIChsYXJnZSBkZXBlbmRlbmNpZXMpXHJcbiAgICAgICAgICAndmlkZW8tdmVuZG9yJzogWydobHMuanMnXSxcclxuICAgICAgICAgIC8vIEljb25zIChjYW4gYmUgbGFyZ2UpXHJcbiAgICAgICAgICAnaWNvbnMnOiBbJ2x1Y2lkZS1yZWFjdCddLFxyXG4gICAgICAgIH0sXHJcbiAgICAgICAgLy8gT3B0aW1pemUgY2h1bmsgbmFtZXMgZm9yIGJldHRlciBjYWNoaW5nXHJcbiAgICAgICAgY2h1bmtGaWxlTmFtZXM6ICdhc3NldHMvW25hbWVdLVtoYXNoXS5qcycsXHJcbiAgICAgICAgZW50cnlGaWxlTmFtZXM6ICdhc3NldHMvW25hbWVdLVtoYXNoXS5qcycsXHJcbiAgICAgICAgYXNzZXRGaWxlTmFtZXM6ICdhc3NldHMvW25hbWVdLVtoYXNoXS5bZXh0XScsXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gICAgLy8gSW5jcmVhc2UgY2h1bmsgc2l6ZSB3YXJuaW5nIGxpbWl0XHJcbiAgICBjaHVua1NpemVXYXJuaW5nTGltaXQ6IDEwMDAsXHJcbiAgICAvLyBVc2UgZXNidWlsZCBmb3IgZmFzdGVyIG1pbmlmaWNhdGlvblxyXG4gICAgbWluaWZ5OiAnZXNidWlsZCcsXHJcbiAgICAvLyBFbmFibGUgQ1NTIGNvZGUgc3BsaXR0aW5nXHJcbiAgICBjc3NDb2RlU3BsaXQ6IHRydWUsXHJcbiAgICAvLyBTb3VyY2UgbWFwcyBvbmx5IGZvciBlcnJvcnMgKHNtYWxsZXIgYnVpbGQpXHJcbiAgICBzb3VyY2VtYXA6IGZhbHNlLFxyXG4gICAgLy8gT3B0aW1pemUgZGVwZW5kZW5jaWVzXHJcbiAgICBjb21tb25qc09wdGlvbnM6IHtcclxuICAgICAgdHJhbnNmb3JtTWl4ZWRFc01vZHVsZXM6IHRydWUsXHJcbiAgICB9LFxyXG4gIH0sXHJcbiAgcmVzb2x2ZToge1xyXG4gICAgYWxpYXM6IHtcclxuICAgICAgXCJAXCI6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsIFwiLi9zcmNcIiksXHJcbiAgICB9LFxyXG4gICAgZXh0ZW5zaW9uczogWycubWpzJywgJy5qcycsICcubXRzJywgJy50cycsICcuanN4JywgJy50c3gnLCAnLmpzb24nXVxyXG4gIH0sXHJcbiAgc2VydmVyOiB7XHJcbiAgICBwb3J0OiA1MTc0LFxyXG4gICAgcHJveHk6IHtcclxuICAgICAgJy9hcGknOiB7XHJcbiAgICAgICAgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDAwJyxcclxuICAgICAgICBjaGFuZ2VPcmlnaW46IHRydWUsXHJcbiAgICAgIH0sXHJcbiAgICB9LFxyXG4gIH0sXHJcbiAgLy8gT3B0aW1pemUgZGVwZW5kZW5jaWVzXHJcbiAgb3B0aW1pemVEZXBzOiB7XHJcbiAgICBpbmNsdWRlOiBbXHJcbiAgICAgICdyZWFjdCcsXHJcbiAgICAgICdyZWFjdC1kb20nLFxyXG4gICAgICAncmVhY3Qtcm91dGVyLWRvbScsXHJcbiAgICAgICdobHMuanMnLFxyXG4gICAgICAnbHVjaWRlLXJlYWN0J1xyXG4gICAgXSxcclxuICAgIC8vIEV4Y2x1ZGUgbGFyZ2UgZGVwZW5kZW5jaWVzIHRoYXQgZG9uJ3QgbmVlZCBwcmUtYnVuZGxpbmdcclxuICAgIGV4Y2x1ZGU6IFsndmlkZW8uanMnLCAnQHZpZGVvanMvaHR0cC1zdHJlYW1pbmcnXSxcclxuICB9LFxyXG4gIC8vIFBlcmZvcm1hbmNlIG9wdGltaXphdGlvbnNcclxuICBlc2J1aWxkOiB7XHJcbiAgICAvLyBSZW1vdmUgZGVidWdnZXIgc3RhdGVtZW50cyBpbiBwcm9kdWN0aW9uXHJcbiAgICBkcm9wOiBwcm9jZXNzLmVudi5OT0RFX0VOViA9PT0gJ3Byb2R1Y3Rpb24nID8gWydkZWJ1Z2dlcicsICdjb25zb2xlJ10gOiBbXSxcclxuICAgIC8vIE9wdGltaXplIGZvciBzcGVlZFxyXG4gICAgbGVnYWxDb21tZW50czogJ25vbmUnLFxyXG4gIH0sXHJcbn0pXHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBZ1csT0FBTyxVQUFVO0FBQ2pYLFNBQVMscUJBQXFCO0FBQzlCLFNBQVMsb0JBQW9CO0FBQzdCLE9BQU8sV0FBVztBQUNsQixPQUFPLGlCQUFpQjtBQUpxTSxJQUFNLDJDQUEyQztBQU05USxJQUFNLGFBQWEsY0FBYyx3Q0FBZTtBQUNoRCxJQUFNLFlBQVksS0FBSyxRQUFRLFVBQVU7QUFFekMsUUFBUSxJQUFJLDRCQUE0QixTQUFTO0FBQ2pELFFBQVEsSUFBSSxzQkFBc0IsUUFBUSxJQUFJLENBQUM7QUFFL0MsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsTUFBTTtBQUFBLEVBQ04sU0FBUztBQUFBLElBQ1AsTUFBTTtBQUFBLElBQ04sWUFBWTtBQUFBLEVBQ2Q7QUFBQSxFQUNBLE9BQU87QUFBQTtBQUFBLElBRUwsUUFBUTtBQUFBLElBQ1IsZUFBZTtBQUFBLE1BQ2IsT0FBTyxLQUFLLFFBQVEsV0FBVyxZQUFZO0FBQUEsTUFDM0MsUUFBUTtBQUFBO0FBQUEsUUFFTixjQUFjO0FBQUE7QUFBQSxVQUVaLGdCQUFnQixDQUFDLFNBQVMsV0FBVztBQUFBO0FBQUEsVUFFckMsVUFBVSxDQUFDLGtCQUFrQjtBQUFBO0FBQUEsVUFFN0IsZ0JBQWdCLENBQUMsUUFBUTtBQUFBO0FBQUEsVUFFekIsU0FBUyxDQUFDLGNBQWM7QUFBQSxRQUMxQjtBQUFBO0FBQUEsUUFFQSxnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxRQUNoQixnQkFBZ0I7QUFBQSxNQUNsQjtBQUFBLElBQ0Y7QUFBQTtBQUFBLElBRUEsdUJBQXVCO0FBQUE7QUFBQSxJQUV2QixRQUFRO0FBQUE7QUFBQSxJQUVSLGNBQWM7QUFBQTtBQUFBLElBRWQsV0FBVztBQUFBO0FBQUEsSUFFWCxpQkFBaUI7QUFBQSxNQUNmLHlCQUF5QjtBQUFBLElBQzNCO0FBQUEsRUFDRjtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxLQUFLLFFBQVEsV0FBVyxPQUFPO0FBQUEsSUFDdEM7QUFBQSxJQUNBLFlBQVksQ0FBQyxRQUFRLE9BQU8sUUFBUSxPQUFPLFFBQVEsUUFBUSxPQUFPO0FBQUEsRUFDcEU7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQUE7QUFBQSxFQUVBLGNBQWM7QUFBQSxJQUNaLFNBQVM7QUFBQSxNQUNQO0FBQUEsTUFDQTtBQUFBLE1BQ0E7QUFBQSxNQUNBO0FBQUEsTUFDQTtBQUFBLElBQ0Y7QUFBQTtBQUFBLElBRUEsU0FBUyxDQUFDLFlBQVkseUJBQXlCO0FBQUEsRUFDakQ7QUFBQTtBQUFBLEVBRUEsU0FBUztBQUFBO0FBQUEsSUFFUCxNQUFNLFFBQVEsSUFBSSxhQUFhLGVBQWUsQ0FBQyxZQUFZLFNBQVMsSUFBSSxDQUFDO0FBQUE7QUFBQSxJQUV6RSxlQUFlO0FBQUEsRUFDakI7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=

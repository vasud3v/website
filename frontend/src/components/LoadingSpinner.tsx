export default function LoadingSpinner() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-6">
            <div className="relative">
                {/* Logo with pulse animation */}
                <img 
                    src="/logo-icon.svg" 
                    alt="Javcore" 
                    className="w-16 h-20 animate-pulse"
                />
                {/* Spinning ring around logo */}
                <div className="absolute inset-0 -m-4">
                    <div className="animate-spin rounded-full h-24 w-24 border-t-2 border-b-2 border-primary"></div>
                </div>
            </div>
            <p className="text-sm text-muted-foreground font-light tracking-wide">Loading...</p>
        </div>
    );
}

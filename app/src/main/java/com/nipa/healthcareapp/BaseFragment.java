package com.nipa.healthcareapp;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.LayoutRes;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
// Assuming R class is in com.nipa.healthcareapp.R
// import com.nipa.healthcareapp.R;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public abstract class BaseFragment extends Fragment {

    protected View rootView;
    protected View loadingView; // To be initialized by subclass via setupViews, using R.id.loadingView
    protected View errorView;   // To be initialized by subclass via setupViews, using R.id.errorView
    protected View contentView; // To be initialized by subclass via setupViews, using R.id.contentView

    protected Runnable retryAction;

    // Using a single static cached thread pool for all fragments for background tasks.
    private static final ExecutorService backgroundExecutor = Executors.newCachedThreadPool();
    // Handler to post results back to the main thread.
    private final Handler mainThreadHandler = new Handler(Looper.getMainLooper());

    // Callback interface for asynchronous operations
    public interface ApiCallback<T> {
        void onSuccess(T result);
        void onError(Exception e);
    }

    // Abstract method for subclasses to provide their layout resource ID
    @LayoutRes
    protected abstract int getLayoutId();

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        rootView = inflater.inflate(getLayoutId(), container, false);
        // Note: setupViews() is NOT called here automatically.
        // Subclasses are responsible for calling it, typically in onViewCreated.
        return rootView;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        // Example: Subclasses should call this if they rely on the base view fields.
        // setupViews();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        rootView = null; // Clean up view references
        loadingView = null;
        errorView = null;
        contentView = null;
    }

    // Call this in onViewCreated of subclass if using base loading/error/content views
    protected void setupViews() {
        if (rootView == null) return; // Should not happen if called after onCreateView
        // These IDs are assumed based on the Kotlin file.
        // Ensure these IDs are present in the layout provided by getLayoutId().
        loadingView = rootView.findViewById(R.id.loadingView);
        errorView = rootView.findViewById(R.id.errorView);
        contentView = rootView.findViewById(R.id.contentView);
    }

    protected void showLoading(boolean isLoading) {
        if (loadingView != null) loadingView.setVisibility(isLoading ? View.VISIBLE : View.GONE);
        if (contentView != null) contentView.setVisibility(isLoading ? View.GONE : View.VISIBLE);
        if (errorView != null) errorView.setVisibility(View.GONE); // Always hide error view when loading state changes
    }

    // For simple string messages
    protected void showErrorDialog(String message) {
        if (getContext() == null) return;
        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(getString(R.string.error)) // Assuming R.string.error for "Error"
                .setMessage(message)
                .setPositiveButton(getString(android.R.string.ok), (dialog, which) -> dialog.dismiss())
                .show();
    }

    // For Throwables, with retry logic
    protected void showErrorDialog(Throwable throwable) {
        if (getContext() == null) return; // Cannot show dialog without context

        showLoading(false); // Hide loading indicator
        if (contentView != null) contentView.setVisibility(View.GONE); // Hide content
        if (errorView != null) errorView.setVisibility(View.VISIBLE); // Show error placeholder UI if available

        String errorMessageText = throwable.getLocalizedMessage() != null ? throwable.getLocalizedMessage() : "An unexpected error occurred.";

        MaterialAlertDialogBuilder builder = new MaterialAlertDialogBuilder(requireContext());
        builder.setTitle(getString(R.string.error)); // Assuming R.string.error for "Error"
        builder.setMessage(errorMessageText);

        if (retryAction != null) {
            builder.setPositiveButton(getString(R.string.retry), (dialog, which) -> { // Assuming R.string.retry for "Retry"
                dialog.dismiss(); // Dismiss current dialog before retrying
                retryAction.run();
            });
            builder.setNegativeButton(getString(android.R.string.cancel), (dialog, which) -> dialog.dismiss());
        } else {
            builder.setPositiveButton(getString(android.R.string.ok), (dialog, which) -> dialog.dismiss());
        }
        builder.setCancelable(false); // Often errors are modal
        builder.show();
    }

    // Set the retry action for the showError(Throwable) dialog
    protected void setRetryAction(Runnable action) {
        this.retryAction = action;
    }


    protected <T> void safeApiCall(Callable<T> call, ApiCallback<T> callback) {
        backgroundExecutor.execute(() -> {
            try {
                T result = call.call();
                mainThreadHandler.post(() -> callback.onSuccess(result));
            } catch (Exception e) {
                mainThreadHandler.post(() -> callback.onError(e));
            }
        });
    }

    protected <T> void executeWithLoading(Callable<T> call, ApiCallback<T> callback) {
        mainThreadHandler.post(() -> showLoading(true));
        backgroundExecutor.execute(() -> {
            try {
                T result = call.call();
                mainThreadHandler.post(() -> {
                    showLoading(false);
                    callback.onSuccess(result);
                });
            } catch (Exception e) {
                mainThreadHandler.post(() -> {
                    showLoading(false);
                    // Use the showErrorDialog(Throwable) which shows a dialog and handles errorView visibility
                    showErrorDialog(e);
                    callback.onError(e); // Also propagate to specific callback
                });
            }
        });
    }
}

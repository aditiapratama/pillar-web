var gulp          = require('gulp'),
    sass          = require('gulp-sass'),
    sourcemaps    = require('gulp-sourcemaps'),
    autoprefixer  = require('gulp-autoprefixer'),
    jade          = require('gulp-jade'),
    livereload    = require('gulp-livereload');

/* CSS */
gulp.task('styles', function() {
    gulp.src('pillar-web/src/styles/*.sass')
        .pipe(sourcemaps.init())
        .pipe(sass({
            outputStyle: 'compressed'}
            ))
        .pipe(autoprefixer("last 3 version", "safari 5", "ie 8", "ie 9"))
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest('pillar-web/application/static/assets/css'))
        .pipe(livereload());
});

/* Templates - Jade */
gulp.task('templates', function() {
    gulp.src('pillar-web/src/templates/**/*.jade')
        .pipe(jade({
            pretty: true
        }))
        .pipe(gulp.dest('pillar-web/application/templates/'))
        .pipe(livereload());
});

// While developing, run 'gulp watch'
gulp.task('watch',function() {
    livereload.listen();

    gulp.watch('pillar-web/src/styles/*.sass',['styles']);
    gulp.watch('pillar-web/src/templates/*.jade',['templates']);
});

// Run 'gulp' to build everything at once
gulp.task('default', ['styles', 'templates']);

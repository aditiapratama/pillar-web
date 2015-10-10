var gulp          = require('gulp'),
    plumber       = require('gulp-plumber'),
    sass          = require('gulp-sass'),
    sourcemaps    = require('gulp-sourcemaps'),
    autoprefixer  = require('gulp-autoprefixer'),
    jade          = require('gulp-jade'),
    concat        = require('gulp-concat'),
    uglify        = require('gulp-uglify'),
    rename        = require('gulp-rename'),
    livereload    = require('gulp-livereload');


/* CSS */
gulp.task('styles', function() {
    gulp.src('pillar-web/src/styles/**/*.sass')
        .pipe(plumber())
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


/* Individual Uglified Scripts */
gulp.task('scripts', function() {
    gulp.src('pillar-web/src/scripts/*.js')
        .pipe(sourcemaps.init())
        .pipe(uglify())
        .pipe(rename({suffix: '.min'}))
        .pipe(sourcemaps.write("."))
        .pipe(gulp.dest('pillar-web/application/static/assets/js/'))
        .pipe(livereload());
});


/* Collection of scripts in src/scripts/tutti/ to merge into tutti.min.js */
/* Since it's always loaded, it's only for functions that we want site-wide */
gulp.task('scripts_concat_tutti', function() {
    gulp.src('pillar-web/src/scripts/tutti/**/*.js')
        .pipe(sourcemaps.init())
        .pipe(concat("tutti.min.js"))
        .pipe(uglify())
        .pipe(sourcemaps.write("."))
        .pipe(gulp.dest('pillar-web/application/static/assets/js/'))
        .pipe(livereload());
});

gulp.task('scripts_concat_comments', function() {
    gulp.src('pillar-web/src/scripts/comments/*.js')
        .pipe(sourcemaps.init())
        .pipe(concat("comments.min.js"))
        .pipe(uglify())
        .pipe(gulp.dest('pillar-web/application/static/assets/js/'))
        .pipe(livereload());
});


// While developing, run 'gulp watch'
gulp.task('watch',function() {
    livereload.listen();

    gulp.watch('pillar-web/src/styles/**/*.sass',['styles']);
    gulp.watch('pillar-web/src/templates/**/*.jade',['templates']);
    gulp.watch('pillar-web/src/scripts/*.js',['scripts']);
    gulp.watch('pillar-web/src/scripts/tutti/**/*.js',['scripts_concat_tutti']);
    gulp.watch('pillar-web/src/scripts/comments/**/*.js',['scripts_concat_comments']);
});


// Run 'gulp' to build everything at once
gulp.task('default', ['styles', 'templates', 'scripts', 'scripts_concat_tutti', 'scripts_concat_comments']);

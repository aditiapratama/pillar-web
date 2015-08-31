module.exports = function(grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        jade: {
          compile: {
            options: {
              data: {
                debug: false
              },
              pretty: true,
            },
            files: [{
              expand: true,
              cwd: 'pillar_web/src/jade',
              src: [ '**/*.jade' ],
              dest: 'pillar_web/application/templates',
              ext: '.html'
            }]
          }
        },

        sass: {
            dist: {
                options: {
                    style: 'compressed'
                },
                files: {
                    'pillar_web/application/static/assets/css/main.css': 'pillar_web/src/sass/main.sass'
                }
            }
        },

        autoprefixer: {
            no_dest: { src: 'pillar_web/application/static/assets/css/main.css' }
        },

        watch: {
            files: ['pillar_web/src/sass/main.sass'],
            tasks: ['sass', 'autoprefixer'],
            jade: {
              files: 'pillar_web/src/jade/**/*.jade',
              tasks: [ 'jade' ]
            },
        }
    });

    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-autoprefixer');
    grunt.loadNpmTasks('grunt-contrib-jade');

    grunt.registerTask('default', ['sass', 'autoprefixer', 'jade']);
};

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
              cwd: 'pillar-web/src/jade',
              src: [ '**/*.jade' ],
              dest: 'pillar-web/application/templates',
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
                    'pillar-web/application/static/assets/css/main.css': 'pillar-web/src/sass/main.sass'
                }
            }
        },

        autoprefixer: {
            no_dest: { src: 'pillar-web/application/static/assets/css/main.css' }
        },

        watch: {
            files: ['pillar-web/src/sass/main.sass'],
            tasks: ['sass', 'autoprefixer'],
            jade: {
              files: 'pillar-web/src/jade/**/*.jade',
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
